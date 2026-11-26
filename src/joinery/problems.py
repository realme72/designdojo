"""Loading problem packages from problems/<id>/."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import yaml

from .contract import Contract, load_contract

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBLEMS_DIR = Path(os.environ.get("JOINERY_PROBLEMS", REPO_ROOT / "problems"))

# Suites in run order. "visible" suites show full expected/actual on failure.
SUITES = ("sample", "hidden", "concurrency")
VISIBLE_SUITES = {"sample"}


class ProblemError(LookupError):
    pass


@dataclass
class Problem:
    id: str
    root: Path

    @cached_property
    def meta(self) -> dict:
        return yaml.safe_load((self.root / "problem.yaml").read_text())

    @property
    def title(self) -> str:
        return self.meta.get("title", self.id)

    @cached_property
    def contract(self) -> Contract:
        return load_contract(self.root / "contract.yaml")

    @property
    def concurrency(self) -> bool:
        return "concurrency" in (self.meta.get("tags") or [])

    @property
    def contract_types(self) -> set[str]:
        c = self.contract
        return set(c.interfaces) | set(c.provided)

    @cached_property
    def decision_points(self) -> list[dict]:
        path = self.root / "decision_points.yaml"
        return yaml.safe_load(path.read_text()) or [] if path.exists() else []

    @property
    def statement(self) -> str:
        return (self.root / self.meta.get("statement", "statement.md")).read_text()

    def suite(self, name: str) -> dict:
        """Load a scenario suite, applying the file-level default config."""
        path = self.root / "scenarios" / f"{name}.yaml"
        if not path.exists():
            return {"name": name, "scenarios": []}
        raw = yaml.safe_load(path.read_text()) or {}
        defaults = {k: v for k, v in raw.items() if k != "scenarios"}
        scenarios = []
        seen = set()
        for sc in raw.get("scenarios") or []:
            if sc["name"] in seen:
                raise ProblemError(f"{path}: duplicate scenario {sc['name']!r}")
            seen.add(sc["name"])
            scenarios.append({**defaults, **sc})
        return {"name": name, "scenarios": scenarios}


JAVA_RESERVED = set("""abstract assert boolean break byte case catch char class const continue default do double
else enum extends final finally float for goto if implements import instanceof int interface long native new
package private protected public return short static strictfp super switch synchronized this throw throws
transient try void volatile while true false null var record yield sealed permits""".split())
PY_RESERVED = set("""False None True and as assert async await break class continue def del elif else except
finally for from global if import in is lambda nonlocal not or pass raise return try while with yield
self cls""".split())

CATEGORIES = {"Booking & reservations", "Commerce & payments", "Data structures & caching", "Games",
              "Infrastructure & control", "Scheduling & workflows", "Social & content"}
DIFFICULTIES = {"easy", "medium", "hard"}

STEP_KEYS = {"call", "args", "expect", "expect_error", "bind", "advance_clock", "parallel", "assert"}


def _type_issue(value, t: dict, c: Contract, path: str) -> str | None:
    """Does a scenario literal fit the contract type? (References/templates are skipped.)"""
    if isinstance(value, str) and ("$" in value or "{i" in value):
        return None
    k = t["kind"]
    if value is None:
        return f"{path}: null for {k}"
    if k == "str":
        return None if isinstance(value, str) else f"{path}: expected a string, YAML gave {value!r}"
    if k in ("int", "long"):
        return None if isinstance(value, int) and not isinstance(value, bool) else f"{path}: expected {k}, got {value!r}"
    if k == "bool":
        return None if isinstance(value, bool) else f"{path}: expected bool, got {value!r}"
    if k == "enum":
        return None if value in c.enums[t["name"]] else f"{path}: {value!r} is not a {t['name']}"
    if k == "list":
        if not isinstance(value, list):
            return f"{path}: expected a list"
        return next((e for i, v in enumerate(value) if (e := _type_issue(v, t["of"], c, f"{path}[{i}]"))), None)
    if k == "map":
        if not isinstance(value, dict):
            return f"{path}: expected a map"
        for key, v in value.items():
            if t["key"]["kind"] == "enum" and key not in c.enums[t["key"]["name"]]:
                return f"{path}: key {key!r} is not a {t['key']['name']}"
            if e := _type_issue(v, t["value"], c, f"{path}.{key}"):
                return e
        return None
    if k == "dto":
        if not isinstance(value, dict):
            return f"{path}: expected a {t['name']} map"
        fields = {f.name: f.type for f in c.dtos[t["name"]]}
        missing = set(fields) - set(value)
        extra = set(value) - set(fields)
        if missing or extra:
            return f"{path}: {t['name']} fields missing {sorted(missing)} / unknown {sorted(extra)}"
        return next((e for n, v in value.items() if (e := _type_issue(v, fields[n], c, f"{path}.{n}"))), None)
    return None


def lint_problem(p: Problem) -> list[str]:
    """Static checks that catch authoring mistakes before anything runs."""
    issues: list[str] = []
    try:
        c = p.contract
    except Exception as e:  # noqa: BLE001
        return [f"contract: {e}"]
    for key in ("title", "difficulty", "category"):
        if key not in p.meta:
            issues.append(f"problem.yaml: missing {key}")
    if p.meta.get("category") not in CATEGORIES:
        issues.append(f"problem.yaml: category must be one of {sorted(CATEGORIES)}")
    if p.meta.get("difficulty") not in DIFFICULTIES:
        issues.append(f"problem.yaml: difficulty must be one of {sorted(DIFFICULTIES)}")
    if p.meta.get("id") != p.id:
        issues.append(f"problem.yaml: id {p.meta.get('id')!r} must match the folder name {p.id!r}")
    from .contract import snake_to_camel

    names = [(f"field {d}.{f.name}", f.name) for d, fs in c.dtos.items() for f in fs]
    for group in (c.interfaces, c.provided):
        for iname, methods in group.items():
            for m in methods.values():
                names.append((f"method {iname}.{m.name}", m.name))
                names += [(f"param {iname}.{m.name}({p.name})", p.name) for p in m.params]
    names += [(f"entrypoint param {p.name}", p.name) for p in c.entrypoint.params]
    for what, n in names:
        if snake_to_camel(n) in JAVA_RESERVED or n in PY_RESERVED:
            issues.append(f"contract: {what} is a reserved word in Java or Python")
    iface = c.interfaces[c.entrypoint.returns["name"]]
    entry_params = {x.name for x in c.entrypoint.params if not (x.type.get("kind") == "iface")}
    seen: set[str] = set()
    for suite in SUITES:
        try:
            data = p.suite(suite)
        except Exception as e:  # noqa: BLE001 - surface YAML/shape errors as lint issues
            issues.append(f"scenarios/{suite}.yaml: {str(e).splitlines()[0]} ({type(e).__name__})")
            continue
        if suite == "sample" and not data["scenarios"]:
            issues.append("scenarios/sample.yaml: no scenarios")
        for sc in data["scenarios"]:
            where = f"{suite}/{sc.get('name', '?')}"
            if sc["name"] in seen:
                issues.append(f"{where}: scenario name used in more than one suite")
            seen.add(sc["name"])
            for prm in entry_params:
                if prm not in sc:
                    issues.append(f"{where}: missing entrypoint argument {prm!r}")
                else:
                    ptype = next(x.type for x in c.entrypoint.params if x.name == prm)
                    if e := _type_issue(sc[prm], ptype, c, f"{where} {prm}"):
                        issues.append(e)
            for i, st in enumerate(sc.get("steps") or [], 1):
                unknown = set(st) - STEP_KEYS
                if unknown:
                    issues.append(f"{where} step {i}: unknown keys {sorted(unknown)}")
                if "parallel" in st and "concurrency" not in (p.meta.get("tags") or []):
                    issues.append(f"{where} step {i}: parallel steps need the 'concurrency' tag "
                                  "(otherwise non-thread-safe solutions fail unfairly)")
                call = st.get("call") or (st.get("parallel") or {}).get("call")
                if call is not None:
                    if call not in iface:
                        issues.append(f"{where} step {i}: {call!r} is not a method of {c.entrypoint.returns['name']}")
                        continue
                    args = st.get("args") or (st.get("parallel") or {}).get("args") or {}
                    want = {x.name for x in iface[call].params}
                    if set(args) != want:
                        issues.append(f"{where} step {i}: {call} args {sorted(args)} != contract {sorted(want)}")
                    for prm in iface[call].params:
                        if prm.name in args and (e := _type_issue(args[prm.name], prm.type, c,
                                                                  f"{where} step {i} {call}.{prm.name}")):
                            issues.append(e)
                err = st.get("expect_error")
                if err is not None and err not in c.errors:
                    issues.append(f"{where} step {i}: unknown error {err!r}")
    if (p.meta.get("tags") and "concurrency" in p.meta["tags"]) != bool(p.suite("concurrency")["scenarios"]):
        issues.append("tag 'concurrency' and scenarios/concurrency.yaml must go together")
    try:
        p.decision_points
    except Exception as e:  # noqa: BLE001
        return issues + [f"decision_points.yaml: {str(e).splitlines()[0]} ({type(e).__name__})"]
    ids = [d["id"] for d in p.decision_points]
    if not ids:
        issues.append("decision_points.yaml: missing or empty")
    for d in p.decision_points:
        for k in ("id", "question", "good"):
            if k not in d:
                issues.append(f"decision point {d.get('id', '?')}: missing {k}")
    if not (p.root / "reference" / "python" / "solution").is_dir():
        issues.append("reference/python/solution missing")
    return issues


def list_problems() -> list[Problem]:
    if not PROBLEMS_DIR.is_dir():
        return []
    return [Problem(p.name, p) for p in sorted(PROBLEMS_DIR.iterdir()) if (p / "problem.yaml").exists()]


def get_problem(problem_id: str) -> Problem:
    root = PROBLEMS_DIR / problem_id
    if not (root / "problem.yaml").exists():
        known = ", ".join(p.id for p in list_problems()) or "none"
        raise ProblemError(f"unknown problem {problem_id!r} (available: {known})")
    return Problem(problem_id, root)
