"""SQL console: run any statement against the learner's schema, filled with the data a sample
scenario creates through the learner's own operations. Everything is rolled back afterwards."""

from __future__ import annotations

import time
from pathlib import Path

import psycopg

from . import pg
from .judge import Failure, Scenario, describe
from .params import is_blank, to_pyformat
from .plan import describe_plan, is_read_only, load_indexes, single_statement
from .scaffold import schema_source

MAX_ROWS = 200


def scenarios(ws) -> list[str]:
    return [sc["name"] for sc in ws.problem.suite("sample")["scenarios"]]


def run_console(ws, sql: str, scenario: str | None) -> dict:
    spec = ws.problem.sql_spec
    schema_path, schema_sql = schema_source(ws)
    if is_blank(sql):
        return {"error": "nothing to run"}
    sources = {name: f.read_text() for name in spec.operations
               if (f := Path(ws.root) / "solution" / "ops" / f"{name}.sql").exists()}
    out: dict = {"scenario": scenario, "data_note": None}
    with pg.job_database() as dsn, pg.connect(dsn) as conn:
        cur = conn.cursor()
        try:
            cur.execute(schema_sql)
        except psycopg.Error as e:
            return {"error": f"{schema_path} does not apply: {describe(e)}"}
        if scenario:
            sc = next((s for s in ws.problem.suite("sample")["scenarios"] if s["name"] == scenario), None)
            if sc is None:
                return {"error": f"unknown sample scenario {scenario!r}"}
            runner = Scenario(ws, conn, sc, spec.operations, sources)
            try:
                runner.run()
                out["data_note"] = f"Data: tables filled by your operations in sample scenario '{scenario}'."
            except Failure as f:
                out["data_note"] = (f"Data: scenario '{scenario}' stopped at step {f.d['step']} "
                                    f"({f.d['message'][:160]}); tables hold what was created before that.")
        stmt = single_statement(sql)
        cur.execute("savepoint console")
        try:
            if stmt is not None and is_read_only(stmt):
                cur.execute("analyze")
                cur.execute("explain (analyze, format json) " + stmt)
                plan_json = cur.fetchone()[0]
                out["plan"] = describe_plan(plan_json, stmt, True, load_indexes(cur))
            t0 = time.monotonic()
            cur.execute(to_pyformat(sql), {})
            last = None
            while True:
                if cur.description:
                    last = ([d.name for d in cur.description], cur.fetchmany(MAX_ROWS + 1), cur.rowcount)
                if not cur.nextset():
                    break
            out["ms"] = round((time.monotonic() - t0) * 1000, 1)
            if last:
                from .judge import norm

                cols, rows, _ = last
                out["columns"] = cols
                out["rows"] = [[norm(v) for v in r] for r in rows[:MAX_ROWS]]
                out["truncated"] = len(rows) > MAX_ROWS
            else:
                out["message"] = f"OK ({cur.rowcount} row(s) affected; rolled back)"
            if stmt is None:
                out["plan_note"] = "Several statements: the flow view needs a single statement."
            elif not is_read_only(stmt):
                out["plan_note"] = "Writes are not visualised here (EXPLAIN ANALYZE would run them twice)."
        except psycopg.Error as e:
            out["error"] = describe(e)
            pos = e.diag.statement_position
            if pos:
                out["error_line"] = sql.count("\n", 0, int(pos) - 1) + 1
        finally:
            conn.rollback()
    return out
