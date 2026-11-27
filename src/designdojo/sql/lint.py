"""Authoring checks for SQL problem packages."""

from __future__ import annotations

import psycopg.errors

from .params import param_names
from .spec import PARAM_TYPES, RETURNS, literal_issue

SQL_CATEGORIES = {"Social & content", "Commerce & payments", "Booking & reservations", "Transport & logistics",
                  "SaaS & productivity", "SQL queries"}
STEP_KEYS = {"op", "args", "expect", "expect_error", "bind", "sql"}


def known_error(name: str) -> bool:
    if name in ("constraint", "rejected"):
        return True
    camel = "".join(p.capitalize() for p in name.split("_"))
    return hasattr(psycopg.errors, camel)


def lint_sql_problem(p) -> list[str]:
    from ..problems import DIFFICULTIES

    issues: list[str] = []
    for key in ("title", "difficulty", "category"):
        if key not in p.meta:
            issues.append(f"problem.yaml: missing {key}")
    if p.meta.get("category") not in SQL_CATEGORIES:
        issues.append(f"problem.yaml: category must be one of {sorted(SQL_CATEGORIES)}")
    if p.meta.get("difficulty") not in DIFFICULTIES:
        issues.append(f"problem.yaml: difficulty must be one of {sorted(DIFFICULTIES)}")
    if p.meta.get("id") != p.id:
        issues.append(f"problem.yaml: id must match the folder name {p.id!r}")
    try:
        spec = p.sql_spec
    except Exception as e:  # noqa: BLE001
        return issues + [f"spec.yaml: {e}"]
    if spec.schema not in ("designed", "provided"):
        issues.append("spec.yaml: schema must be designed or provided")
    if spec.schema == "provided" and not (p.root / "schema.sql").exists():
        issues.append("schema.sql missing (schema: provided)")
    if not spec.operations:
        issues.append("spec.yaml: no operations")
    ref = p.root / "reference" / "sql" / "solution"
    for name, op in spec.operations.items():
        if op.returns not in RETURNS:
            issues.append(f"op {name}: returns must be one of {sorted(RETURNS)}")
        for prm, t in op.params.items():
            if t not in PARAM_TYPES:
                issues.append(f"op {name}: param {prm} has unknown type {t!r}")
        if op.returns in ("one", "rows") and not op.columns:
            issues.append(f"op {name}: list the result columns")
        f = ref / "ops" / f"{name}.sql"
        if not f.exists():
            issues.append(f"reference op {name}.sql missing")
        else:
            used = set(param_names(f.read_text()))
            if used - set(op.params):
                issues.append(f"reference op {name}.sql uses undeclared params {sorted(used - set(op.params))}")
    if spec.schema == "designed" and not (ref / "schema.sql").exists():
        issues.append("reference/sql/solution/schema.sql missing")
    seen: set[str] = set()
    for suite in ("sample", "hidden"):
        try:
            data = p.suite(suite)
        except Exception as e:  # noqa: BLE001
            issues.append(f"{suite} scenarios: {str(e).splitlines()[0]}")
            continue
        if suite == "sample" and not data["scenarios"]:
            issues.append("scenarios/sample.yaml: no scenarios")
        for sc in data["scenarios"]:
            where = f"{suite}/{sc['name']}"
            if sc["name"] in seen:
                issues.append(f"{where}: scenario name used in more than one suite")
            seen.add(sc["name"])
            if "seed" in sc and spec.schema != "provided":
                issues.append(f"{where}: seed SQL only works with a provided schema; use operations")
            for i, st in enumerate(sc.get("steps") or [], 1):
                if set(st) - STEP_KEYS:
                    issues.append(f"{where} step {i}: unknown keys {sorted(set(st) - STEP_KEYS)}")
                if "sql" in st:
                    if spec.schema != "provided":
                        issues.append(f"{where} step {i}: raw sql steps need a provided schema")
                    continue
                op = spec.operations.get(st.get("op"))
                if op is None:
                    issues.append(f"{where} step {i}: unknown op {st.get('op')!r}")
                    continue
                args = st.get("args") or {}
                if set(args) != set(op.params):
                    issues.append(f"{where} step {i}: {op.name} args {sorted(args)} != {sorted(op.params)}")
                for k, t in op.params.items():
                    if k in args and (e := literal_issue(args[k], t)):
                        issues.append(f"{where} step {i} {op.name}.{k}: {e}")
                if "expect_error" in st and not known_error(st["expect_error"]):
                    issues.append(f"{where} step {i}: unknown error {st['expect_error']!r} "
                                  "(use a Postgres condition name like unique_violation, or constraint/rejected)")
                if "expect" in st and op.returns == "none":
                    issues.append(f"{where} step {i}: {op.name} returns none; nothing to expect")
    if not p.decision_points:
        issues.append("decision_points.yaml: missing or empty")
    from .questions import lint_questions

    issues += lint_questions(p)
    return issues
