"""Judge SQL problems against Postgres.

Per run: a fresh database. Per scenario: a fresh Postgres schema (namespace) holding the
learner's tables, dropped afterwards, so scenarios are isolated and identity columns restart
at 1. Per operation: its own transaction that COMMITS, exactly like a real request - so
deferred constraints and constraint triggers are checked, and a rejected operation is rolled
back without affecting the rest of the scenario.
Result shape matches the code runners, so reports, history and the UI work unchanged.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
from decimal import Decimal
from pathlib import Path

import psycopg
import psycopg.errors

from . import pg
from .params import is_blank, line_of, to_pyformat, transaction_control
from .plan import describe_plan, is_read_only, load_indexes, single_statement
from .scaffold import schema_source
from .spec import Operation, convert

# expect_error aliases: a requirement can usually be enforced more than one way
ALIASES = {
    "constraint": lambda st: st.startswith("23"),
    # any integrity/data error or a RAISE from a trigger/function: the DB refused the change
    "rejected": lambda st: st.startswith(("23", "22")) or st == "P0001",
}


def error_name(e: psycopg.Error) -> str:
    st = e.sqlstate or ""
    cls = psycopg.errors.lookup(st) if st else None
    name = cls.__name__ if cls else type(e).__name__
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def error_matches(want: str, e: psycopg.Error) -> bool:
    if want in ALIASES:
        return ALIASES[want](e.sqlstate or "")
    return error_name(e) == want


def describe(e: psycopg.Error) -> str:
    d = e.diag
    msg = d.message_primary or str(e).splitlines()[0]
    extra = f" (constraint {d.constraint_name})" if d.constraint_name else ""
    return f"{error_name(e)}: {msg}{extra}"


def norm(v):
    """DB value -> JSON-comparable value."""
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, dt.datetime):
        return v.isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    return v


def matches(exp, act) -> bool:
    if isinstance(exp, dict):
        return isinstance(act, dict) and all(k.lower() in act and matches(v, act[k.lower()]) for k, v in exp.items())
    if isinstance(exp, list):
        return isinstance(act, list) and len(exp) == len(act) and all(matches(a, b) for a, b in zip(exp, act))
    if isinstance(exp, bool) or isinstance(act, bool):
        return exp is act
    if isinstance(exp, (int, float)) and isinstance(act, (int, float)):
        return abs(exp - act) < 1e-6
    if isinstance(exp, (dt.date, dt.datetime)):
        exp = exp.isoformat()
    return exp == act


def multiset_match(exp: list, act: list) -> bool:
    if len(exp) != len(act):
        return False
    used = [False] * len(act)
    for e in exp:
        for i, a in enumerate(act):
            if not used[i] and matches(e, a):
                used[i] = True
                break
        else:
            return False
    return True


class Failure(Exception):
    def __init__(self, step: int, kind: str, message: str, expected=None, actual=None, has_ea: bool = False):
        super().__init__(message)
        self.d = {"step": step, "kind": kind, "message": message}
        if has_ea:
            self.d.update(expected=expected, actual=actual)


class Scenario:
    def __init__(self, ws, conn: psycopg.Connection, sc: dict, ops: dict[str, Operation], sources: dict[str, str],
                 explain: bool = False):
        self.ws, self.conn, self.sc, self.ops, self.sources = ws, conn, sc, ops, sources
        self.vars: dict = {}
        self.explain = explain
        self.plans: list[dict] = []

    # ---- references: "$name.field[0].x"
    def lookup(self, ref: str):
        m = re.match(r"\$(\w+)(.*)", ref)
        val = self.vars[m.group(1)]
        for part in re.findall(r"\.(\w+)|\[(\d+)\]", m.group(2)):
            val = val[part[0].lower()] if part[0] else val[int(part[1])]
        return val

    def resolve(self, v):
        if isinstance(v, str) and v.startswith("$"):
            return self.lookup(v)
        if isinstance(v, list):
            return [self.resolve(x) for x in v]
        if isinstance(v, dict):
            return {k: self.resolve(x) for k, x in v.items()}
        return v

    def run(self, until: int | None = None) -> None:
        cur = self.conn.cursor()
        for sql in filter(None, [self.sc.get("seed")]):
            cur.execute(sql)
            self.conn.commit()
        for n, st in enumerate(self.sc.get("steps") or [], 1):
            if until is not None and n > until:
                break
            self.step(n, st)

    def capture_plan(self, n: int, name: str, sql: str, args: dict, call: str) -> None:
        """EXPLAIN the operation on this scenario's data, as the learner's query-flow view.
        Read-only statements are EXPLAIN ANALYZEd (real row counts); writes get estimates only."""
        stmt = single_statement(sql)
        entry = {"step": n, "op": name, "call": call}
        if stmt is None:
            entry["note"] = "Several statements: only single-statement operations are visualised."
            self.plans.append(entry)
            return
        analyze = is_read_only(stmt)
        cur = self.conn.cursor()
        try:
            cur.execute("analyze")  # fresh statistics, so estimates reflect the scenario's data
            cur.execute(to_pyformat(f"explain (analyze {str(analyze).lower()}, format json) {stmt}"), args)
            plan_json = cur.fetchone()[0]
            entry["plan"] = describe_plan(plan_json, stmt, analyze, load_indexes(cur))
        except psycopg.Error as e:
            entry["note"] = f"could not explain: {describe(e)}"
        finally:
            self.conn.rollback()  # EXPLAIN ANALYZE ran the statement: undo it
        self.plans.append(entry)

    def _exec(self, sql: str, args: dict):
        """Run as one committed transaction; returns (columns, rows) of the last result set.
        Deferred constraints fire at COMMIT, so a failure there rejects the operation too."""
        cur = self.conn.cursor()
        try:
            cur.execute(to_pyformat(sql), args)
            last = None
            while True:
                if cur.description:
                    last = ([d.name.lower() for d in cur.description], cur.fetchall())
                if not cur.nextset():
                    break
            self.conn.commit()
        except psycopg.Error:
            self.conn.rollback()
            raise
        return last

    def step(self, n: int, st: dict) -> None:
        if "sql" in st:  # authoring-only: raw statements (provided-schema problems)
            self._exec(st["sql"], {})
            return
        name = st["op"]
        op = self.ops[name]
        sql = self.sources.get(name)
        if sql is None or is_blank(sql):
            raise Failure(n, "missing_method", f"solution/ops/{name}.sql is not implemented yet")
        if (tc := transaction_control(sql)):
            raise Failure(n, "unexpected_error", f"{name}: remove {tc} from ops/{name}.sql; every operation "
                                                 "already runs atomically inside the judge's transaction")
        raw_args = self.resolve(st.get("args") or {})
        args = {k: convert(raw_args.get(k), t) for k, t in op.params.items()}
        call = f"{name}({', '.join(f'{k}={json.dumps(v, default=str)}' for k, v in raw_args.items())})"
        if self.explain and op.kind == "query" and "expect_error" not in st:
            self.capture_plan(n, name, sql, args, call)
        try:
            out = self._exec(sql, args)
        except psycopg.errors.QueryCanceled:
            raise Failure(n, "timeout", f"{call} exceeded {pg.STATEMENT_TIMEOUT_MS} ms "
                                        "(missing index, accidental cross join, or waiting on a lock?)") from None
        except psycopg.Error as e:
            if "expect_error" in st:
                if error_matches(st["expect_error"], e):
                    return
                raise Failure(n, "expected_error", f"{call} should be rejected with {st['expect_error']}, "
                                                   f"but failed with {describe(e)}",
                              {"error": st["expect_error"]}, {"error": error_name(e)}, True) from None
            raise Failure(n, "unexpected_error", f"{call} threw {describe(e)} at solution/ops/{name}.sql") from None
        if "expect_error" in st:
            no_row = op.returns == "one" and (out is None or not out[1])
            if no_row and st["expect_error"] == "rejected":
                return  # refusing by returning no row is a valid way to say no (like a 404)
            raise Failure(n, "expected_error", f"{call} should be rejected with {st['expect_error']}, but it "
                                               "succeeded. Which constraint should stop it?",
                          {"error": st["expect_error"]}, {"ok": self._shape(op, out, n, call, lenient=True)}, True)
        value = self._shape(op, out, n, call)
        if "bind" in st:
            self.vars[st["bind"]] = value
        if "expect" in st:
            want = self.resolve(st["expect"])
            ok = (multiset_match(want, value) if op.returns == "rows" and not op.ordered and isinstance(want, list)
                  else matches(want, value))
            if not ok:
                hint = "" if op.returns != "rows" or not op.ordered else " (order matters)"
                raise Failure(n, "wrong_result", f"{call} returned an unexpected result{hint}", want, value, True)

    def _shape(self, op: Operation, out, n: int, call: str, lenient: bool = False):
        if op.returns == "none":
            return None
        cols, rows = out if out else ([], [])
        rows = [{c: norm(v) for c, v in zip(cols, r)} for r in rows]
        if lenient:
            return rows
        if out is None:
            raise Failure(n, "wrong_result", f"{call} returned no result set; expected {op.result_text()}")
        missing = [c for c in op.columns if c.lower() not in cols]
        if missing and op.returns in ("one", "rows"):
            raise Failure(n, "wrong_result", f"{call}: result is missing column(s) {', '.join(missing)} "
                                             f"(got {', '.join(cols) or 'none'}); alias them with AS")
        if op.returns == "rows":
            return rows
        if len(rows) != 1:
            raise Failure(n, "wrong_result", f"{call} returned {len(rows)} rows; expected exactly one",
                          "1 row", rows[:5], True)
        return rows[0] if op.returns == "one" else next(iter(rows[0].values()))


def _schema_diagnostic(path: str, sql: str, e: psycopg.Error) -> dict:
    pos = e.diag.statement_position
    line = line_of(sql, int(pos) - 1) if pos else 0
    if not line:  # e.g. undefined_table has no position: find the first line naming the quoted object
        m = re.search(r'"([^"]+)"', e.diag.message_primary or "")
        if m:
            hit = re.search(rf"\b{re.escape(m.group(1))}\b", sql, re.I)
            line = line_of(sql, hit.start()) if hit else 0
    return {"file": path, "line": line, "message": describe(e)}


def run(ws, suites: list[str]) -> dict:
    problem = ws.problem
    spec = problem.sql_spec
    schema_path, schema_sql = schema_source(ws)
    sources = {}
    for name in spec.operations:
        f = Path(ws.root) / "solution" / "ops" / f"{name}.sql"
        if f.exists():
            sources[name] = f.read_text()
    if spec.schema == "designed" and is_blank(schema_sql):
        return {"status": "compile_error",
                "diagnostics": [{"file": schema_path, "line": 1, "message": "schema.sql is empty: create your tables"}]}
    if (tc := transaction_control(schema_sql)):
        return {"status": "compile_error", "diagnostics": [{"file": schema_path, "line": 1,
                "message": f"remove {tc}: the judge runs the schema inside its own transaction"}]}

    with pg.job_database() as dsn, pg.connect(dsn) as conn:
        # compile check: does the schema apply at all?
        try:
            conn.cursor().execute(schema_sql)
        except psycopg.Error as e:
            conn.rollback()
            return {"status": "compile_error", "diagnostics": [_schema_diagnostic(schema_path, schema_sql, e)]}
        conn.rollback()
        seq = 0

        out = []
        for name in suites:
            suite = problem.suite(name)
            cases, passed = [], 0
            for sc in suite["scenarios"]:
                t0 = time.monotonic()
                scenario = Scenario(ws, conn, sc, spec.operations, sources, explain=name == "sample")
                seq += 1
                ns = f"scenario_{seq}"
                try:
                    cur = conn.cursor()
                    cur.execute(f"create schema {ns}")
                    cur.execute(f"set search_path to {ns}")
                    cur.execute(schema_sql)
                    conn.commit()
                    scenario.run()
                    case = {"name": sc["name"], "status": "pass", "ms": int((time.monotonic() - t0) * 1000)}
                    passed += 1
                except Failure as f:
                    case = {"name": sc["name"], "status": "fail", **f.d}
                except psycopg.Error as e:  # seed/raw step failed: an authoring problem, or schema drift
                    case = {"name": sc["name"], "status": "fail", "step": 0, "kind": "harness_error",
                            "message": describe(e)}
                finally:
                    conn.rollback()
                    cur = conn.cursor()
                    cur.execute(f"drop schema if exists {ns} cascade")
                    cur.execute("set search_path to public")
                    conn.commit()
                if scenario.plans:  # sample suite only: visible to the learner
                    case["plans"] = scenario.plans
                cases.append(case)
            out.append({"name": name, "passed": passed, "total": len(cases), "cases": cases})
        return {"status": "ok", "suites": out}
