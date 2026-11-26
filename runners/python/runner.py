"""Executes scenario suites against a Python solution.

Inputs:  $JOB/contract.json, $JOB/scenarios.json, $JOB/contract/__init__.py (generated),
         $WORK/solution/ (user code, read-only).
Output:  $JOB/result.json

Semantics must stay identical to runners/java/src/joinery/runner/Runner.java.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import os
import random
import re
import sys
import threading
import time
import traceback
from enum import Enum

JOB = os.environ.get("JOINERY_JOB", "/job")
WORK = os.environ.get("JOINERY_WORK", "/work")
START_TIME = 1_700_000_000
CASE_TIMEOUT = float(os.environ.get("JOINERY_CASE_TIMEOUT_MS", "5000")) / 1000
# The GIL hides most races at the default 5 ms switch interval; switch threads
# far more often while parallel steps run so check-then-act bugs surface.
PARALLEL_SWITCH_INTERVAL = 1e-6
# Even then, short methods finish inside one GIL slice. During parallel steps a
# trace hook yields the GIL between lines of *solution* code with this
# probability ("chaos scheduling"), so interleavings look like real cores.
CHAOS_YIELD_P = float(os.environ.get("JOINERY_CHAOS_P", "0.3"))

SPEC: dict = {}
C = None  # generated contract module
S = None  # user solution package


class HarnessError(Exception):
    pass


class Failure(Exception):
    def __init__(self, step, kind, message, expected=..., actual=...):
        super().__init__(message)
        self.d = {"step": step, "kind": kind, "message": message}
        if expected is not ...:
            self.d["expected"] = expected
            self.d["actual"] = actual


# ------------------------------------------------------------------ main


def main() -> None:
    global SPEC, C, S
    try:
        with open(os.path.join(JOB, "contract.json")) as f:
            SPEC = json.load(f)
        with open(os.path.join(JOB, "scenarios.json")) as f:
            plan = json.load(f)
        sys.path[:0] = [JOB, WORK]
        try:
            C = importlib.import_module("contract")
            S = importlib.import_module("solution")
        except SyntaxError as e:
            result = {"status": "compile_error", "diagnostics": [
                {"file": _display(e.filename or ""), "line": e.lineno or 0, "message": f"SyntaxError: {e.msg}"}]}
        except Exception as e:  # noqa: BLE001 - user import failures
            result = {"status": "compile_error", "diagnostics": [
                {"file": _where_file(e), "line": _where_line(e), "message": f"{type(e).__name__}: {e}"}]}
        else:
            result = {"status": "ok", "suites": [run_suite(s) for s in plan["suites"]]}
    except Exception:  # noqa: BLE001
        result = {"status": "harness_error", "message": traceback.format_exc()[-4000:]}
    with open(os.path.join(JOB, "result.json"), "w") as f:
        json.dump(result, f)
    sys.stdout.flush()
    os._exit(0)  # don't wait on stuck user threads


def run_suite(suite: dict) -> dict:
    cases, passed, poisoned = [], 0, False
    for sc in suite["scenarios"]:
        if poisoned:
            cases.append({"name": sc["name"], "status": "skipped", "kind": "skipped",
                          "message": "not run: an earlier scenario timed out and its threads are still running"})
            continue
        r = run_repeated(sc)
        if r["status"] == "pass":
            passed += 1
        elif r.get("kind") == "timeout":
            poisoned = True  # python threads can't be killed; a spinning one would skew the rest
        cases.append(r)
    return {"name": suite["name"], "passed": passed, "total": len(cases), "cases": cases}


def run_repeated(sc: dict) -> dict:
    repeat = int(sc.get("repeat", 1))
    t0 = time.monotonic()
    for it in range(1, repeat + 1):
        f = run_with_timeout(sc)
        if f is not None:
            r = dict(f)
            r.update(name=sc["name"], status="fail")
            if repeat > 1:
                r.update(iteration=it, repeat=repeat)
            return r
    return {"name": sc["name"], "status": "pass", "ms": int((time.monotonic() - t0) * 1000)}


def run_with_timeout(sc: dict) -> dict | None:
    box: list = []

    def target():
        try:
            Scenario(sc).run()
            box.append(None)
        except Failure as f:
            box.append(f.d)
        except Exception:  # noqa: BLE001
            box.append({"step": 0, "kind": "harness_error", "message": traceback.format_exc()[-4000:]})

    t = threading.Thread(target=target, name="scenario", daemon=True)
    t.start()
    t.join(CASE_TIMEOUT)
    if t.is_alive():
        return {"step": 0, "kind": "timeout",
                "message": f"scenario exceeded {int(CASE_TIMEOUT * 1000)} ms (deadlock or infinite loop?)"}
    return box[0]


# ------------------------------------------------------------------ scenario


class Outcome:
    __slots__ = ("value", "json", "error", "unexpected")

    def __init__(self):
        self.value = self.json = self.error = self.unexpected = None

    def describe(self) -> str:
        if self.unexpected:
            return self.unexpected
        if self.error:
            return f"raised {self.error}"
        return "returned " + json.dumps(self.json)

    def as_json(self):
        return {"error": self.error} if self.error else self.json

    def as_result(self):
        if self.unexpected:
            return {"error": "Unexpected", "detail": self.unexpected}
        return {"error": self.error} if self.error else {"ok": self.json}


class Scenario:
    def __init__(self, sc: dict):
        self.sc = sc
        self.now = START_TIME
        self.vars: dict = {}
        self.system = None

    def run(self) -> None:
        ep = SPEC["entrypoint"]
        fn = getattr(S, ep["name"], None)
        if not callable(fn):
            raise Failure(0, "missing_entrypoint", f"solution.{ep['name']}(...) not found")
        args = [
            self.make_provided(p["type"]["name"]) if is_provided(p["type"]) else convert(self.sc.get(p["name"]), p["type"])
            for p in ep["params"]
        ]
        boot = invoke(fn, args, ep["returns"])
        if boot.error:
            raise Failure(0, "unexpected_error", f"{ep['name']}(...) {boot.describe()}")
        if boot.value is None:
            raise Failure(0, "unexpected_error", f"{ep['name']}(...) returned None")
        iface = getattr(C, ep["returns"]["name"])
        if not isinstance(boot.value, iface):
            raise Failure(0, "unexpected_error",
                          f"{ep['name']}(...) returned {type(boot.value).__name__}, which does not subclass contract.{iface.__name__}")
        self.system = boot.value
        for n, st in enumerate(self.sc.get("steps", []), start=1):
            self.step(n, st)

    def step(self, n: int, st: dict) -> None:
        if "advance_clock" in st:
            self.now += int(st["advance_clock"])
        elif "call" in st:
            name = st["call"]
            o = self.call(name, st.get("args", {}), -1)
            if "expect_error" in st:
                want = st["expect_error"]
                if o.error == want and not o.unexpected:
                    return
                raise Failure(n, "expected_error", f"{name} should raise {want} but {o.describe()}",
                              {"error": want}, o.as_json())
            if o.error:
                raise Failure(n, "unexpected_error", f"{name} {o.describe()}")
            if "expect" in st:
                exp = self.resolve(st["expect"], -1)
                if not matches(exp, o.json):
                    raise Failure(n, "wrong_result", f"{name} returned an unexpected value", exp, o.json)
            if "bind" in st:
                self.vars[st["bind"]] = o.json
        elif "parallel" in st:
            self.parallel(st["parallel"])
        elif "assert" in st:
            self.check(n, st["assert"])
        else:
            raise Failure(n, "harness_error", f"unknown step {list(st)}")

    def prepare(self, name: str, raw_args: dict, i: int):
        iface = SPEC["entrypoint"]["returns"]["name"]
        spec = SPEC["interfaces"][iface].get(name)
        if spec is None:
            raise HarnessError(f"contract has no method {name}")
        method = getattr(self.system, name, None)
        if not callable(method):
            raise Failure(0, "missing_method", f"{type(self.system).__name__} has no method {name}")
        args = self.resolve(raw_args, i)
        return method, [convert(args.get(p["name"]), p["type"]) for p in spec["params"]], spec["returns"]

    def call(self, name: str, raw_args: dict, i: int) -> Outcome:
        method, args, returns = self.prepare(name, raw_args, i)
        return invoke(method, args, returns)

    def parallel(self, p: dict) -> None:
        threads = int(p["threads"])
        prepared = [self.prepare(p["call"], p.get("args", {}), k) for k in range(threads)]
        results: list = [None] * threads
        barrier = threading.Barrier(threads)

        def worker(k: int):
            barrier.wait()
            method, args, returns = prepared[k]
            results[k] = invoke(method, args, returns).as_result()

        old = sys.getswitchinterval()
        sys.setswitchinterval(PARALLEL_SWITCH_INTERVAL)
        threading.settrace(_chaos_tracer(random.Random(threads)))
        try:
            ts = [threading.Thread(target=worker, args=(k,), daemon=True) for k in range(threads)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
        finally:
            threading.settrace(None)
            sys.setswitchinterval(old)
        if "collect" in p:
            self.vars[p["collect"]] = results

    def check(self, n: int, a: dict) -> None:
        if "distinct" in a:
            vals = self.resolve(a["distinct"], -1)
            if len({json.dumps(v, sort_keys=True) for v in vals}) != len(vals):
                raise Failure(n, "assertion", "values should all be distinct", {"distinct": True}, vals)
        if "of" not in a:
            return
        rs = self.lookup("$" + a["of"])
        oks = [r["ok"] for r in rs if "ok" in r]
        errs: dict[str, int] = {}
        for r in rs:
            if "error" in r:
                errs[r["error"]] = errs.get(r["error"], 0) + 1
        summary = {"ok_count": len(oks), "error_count": errs}
        if "ok_count" in a and len(oks) != int(a["ok_count"]):
            raise Failure(n, "assertion", "wrong number of successful calls", {"ok_count": a["ok_count"]}, summary)
        for err, want in (a.get("error_count") or {}).items():
            if errs.get(err, 0) != int(want):
                raise Failure(n, "assertion", f"wrong number of {err} errors", {"error_count": a["error_count"]}, summary)
        if "flat_count" in a or "flat_unique" in a:
            items = [x for o in oks if isinstance(o, list) for x in o]
            if "flat_count" in a and len(items) != int(a["flat_count"]):
                raise Failure(n, "assertion", "wrong total number of items across all results",
                              {"flat_count": a["flat_count"]}, {"flat_count": len(items)})
            if "flat_unique" in a:
                f = a["flat_unique"]
                vals = [json.dumps(x if f == "." else x.get(f), sort_keys=True) for x in items]
                dups = sorted({v for v in vals if vals.count(v) > 1})
                if dups:
                    raise Failure(n, "assertion", f"items delivered more than once: {', '.join(dups[:5])}",
                                  {"flat_unique": f}, {"duplicates": [json.loads(d) for d in dups[:5]]})
        if "value_count" in a:
            counts: dict[str, int] = {}
            for o in oks:
                k = json.dumps(o, sort_keys=True)
                counts[k] = counts.get(k, 0) + 1
            for k, want in a["value_count"].items():
                if counts.get(k, 0) != int(want):
                    raise Failure(n, "assertion", f"wrong number of calls returning {k}",
                                  {"value_count": a["value_count"]}, {"value_count": counts})
        if "unique" in a:
            fields = a["unique"] if isinstance(a["unique"], list) else [a["unique"]]
            for f in fields:
                seen = set()
                for o in oks:
                    v = json.dumps(o if f == "." else (o.get(f) if isinstance(o, dict) else None), sort_keys=True)
                    if v in seen:
                        raise Failure(n, "assertion", f"duplicate {f} among successful results: {json.loads(v)}",
                                      {"unique": f}, {"duplicate": json.loads(v)})
                    seen.add(v)

    # ---- references: "$name.field[0].x", with "{i}" templated first

    TOKEN = re.compile(r"\.?([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]")

    def resolve(self, v, i: int):
        if isinstance(v, str):
            if i >= 0:
                v = re.sub(r"\{i(?:\+(\d+))?\}", lambda m: str(i + int(m.group(1) or 0)), v)
            return self.lookup(v) if v.startswith("$") else v
        if isinstance(v, dict):
            return {k: self.resolve(x, i) for k, x in v.items()}
        if isinstance(v, list):
            return [self.resolve(x, i) for x in v]
        return v

    def lookup(self, ref: str):
        body, pos, cur, first = ref[1:], 0, None, True
        for m in self.TOKEN.finditer(body):
            if m.start() != pos:
                raise HarnessError(f"bad reference {ref}")
            pos = m.end()
            if first:
                if m.group(1) not in self.vars:
                    raise HarnessError(f"unbound reference {ref}")
                cur, first = self.vars[m.group(1)], False
            elif m.group(1) is not None:
                if not isinstance(cur, dict):
                    raise HarnessError(f"cannot read .{m.group(1)} in {ref}")
                cur = cur.get(m.group(1))
            else:
                if not isinstance(cur, list):
                    raise HarnessError(f"cannot index in {ref}")
                cur = cur[int(m.group(2))]
        if pos != len(body):
            raise HarnessError(f"bad reference {ref}")
        return cur

    def make_provided(self, name: str):
        base = getattr(C, name)
        if name != "Clock":
            raise HarnessError(f"no harness implementation for provided {name}")
        scenario = self

        class JudgeClock(base):
            def now(self) -> int:
                return scenario.now

            def __repr__(self) -> str:
                return f"JudgeClock({scenario.now})"

        return JudgeClock()


def _chaos_tracer(rng: random.Random):
    solution_prefix = WORK + "/solution"

    def local(frame, event, arg):
        if event == "line" and rng.random() < CHAOS_YIELD_P:
            time.sleep(0)  # releases the GIL: another thread may run between these two lines
        return local

    def on_call(frame, event, arg):
        return local if frame.f_code.co_filename.startswith(solution_prefix) else None

    return on_call


# ------------------------------------------------------------------ invoke & convert


def invoke(fn, args: list, returns: dict) -> Outcome:
    o = Outcome()
    try:
        o.value = fn(*args)
    except Exception as e:  # noqa: BLE001
        name = contract_error(e)
        if name:
            o.error = name
        else:
            o.error = "Unexpected"
            msg = f": {e}" if str(e) else ""
            o.unexpected = f"threw {type(e).__name__}{msg}{_where(e)}"
        return o
    problem = typecheck(o.value, returns)
    if problem:
        o.error = "Unexpected"
        o.unexpected = problem
        return o
    o.json = to_json(o.value)
    return o


def contract_error(e: BaseException) -> str | None:
    for cls in type(e).__mro__:
        if cls.__module__ == "contract" and cls.__name__ in SPEC["errors"]:
            return cls.__name__
    return None


def typecheck(v, t: dict) -> str | None:
    k = t["kind"]
    want = {"int": int, "long": int, "str": str, "bool": bool}.get(k)
    if k == "void":
        return None
    if want is not None:
        if isinstance(v, want) and not (want is int and isinstance(v, bool)):
            return None
        return f"returned {type(v).__name__} {v!r}, contract requires {k}"
    if k in ("enum", "dto", "iface"):
        cls = getattr(C, t["name"])
        if isinstance(v, cls):
            return None
        return f"returned {type(v).__name__}, contract requires contract.{t['name']}"
    if k == "list" and not isinstance(v, (list, tuple)):
        return f"returned {type(v).__name__}, contract requires a list"
    if k == "map" and not isinstance(v, dict):
        return f"returned {type(v).__name__}, contract requires a dict"
    return None


def is_provided(t: dict) -> bool:
    return t["kind"] == "iface" and t["name"] in SPEC["provided"]


def convert(v, t: dict):
    if v is None:
        return None
    k = t["kind"]
    if k in ("int", "long"):
        return int(v)
    if k in ("str", "bool"):
        return v
    if k == "list":
        return [convert(x, t["of"]) for x in v]
    if k == "map":
        kt = t["key"]
        return {(int(key) if kt["kind"] in ("int", "long") else convert(key, kt)): convert(val, t["value"])
                for key, val in v.items()}
    if k == "enum":
        return getattr(C, t["name"])[v]
    if k == "dto":
        cls = getattr(C, t["name"])
        return cls(**{f["name"]: convert(v.get(f["name"]), f["type"]) for f in SPEC["dtos"][t["name"]]})
    raise HarnessError(f"cannot convert to {k}")


def to_json(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, Enum):
        return v.name
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: to_json(getattr(v, f.name)) for f in dataclasses.fields(v)}
    if isinstance(v, (list, tuple, set, frozenset)):
        return [to_json(x) for x in v]
    if isinstance(v, dict):
        return {str(to_json(k)): to_json(x) for k, x in v.items()}
    return str(v)


def matches(exp, act) -> bool:
    if isinstance(exp, dict):
        return isinstance(act, dict) and all(k in act and matches(v, act[k]) for k, v in exp.items())
    if isinstance(exp, list):
        return isinstance(act, list) and len(exp) == len(act) and all(matches(a, b) for a, b in zip(exp, act))
    if isinstance(exp, bool) or isinstance(act, bool):
        return exp is act
    return exp == act


# ------------------------------------------------------------------ locations


def _display(path: str) -> str:
    for prefix in (WORK + "/", JOB + "/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def _solution_frame(e: BaseException):
    frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename.startswith(WORK + "/solution")]
    return frames[-1] if frames else None


def _where(e: BaseException) -> str:
    f = _solution_frame(e)
    return f" at {_display(f.filename)}:{f.lineno}" if f else ""


def _where_file(e: BaseException) -> str:
    f = _solution_frame(e)
    return _display(f.filename) if f else ""


def _where_line(e: BaseException) -> int:
    f = _solution_frame(e)
    return f.lineno if f else 0


if __name__ == "__main__":
    main()
