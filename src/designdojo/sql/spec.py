"""spec.yaml for SQL problems: the operations a solver implements, one .sql file each.

    schema: designed | provided      # provided: schema.sql ships with the problem (query drills)
    operations:
      add_customer:
        doc: Create a customer and return its id.
        params: {email: text, name: text}
        returns: one | rows | value | none
        columns: [id]                 # columns the result must have (one/rows)
        ordered: true                 # rows: does order matter? (default false)
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal

import yaml
from psycopg.types.json import Jsonb

PARAM_TYPES = {"text", "int", "bigint", "numeric", "bool", "date", "timestamptz", "jsonb", "text[]", "int[]"}
RETURNS = {"one", "rows", "value", "none"}


@dataclass
class Operation:
    name: str
    doc: str
    params: dict[str, str]
    returns: str
    columns: list[str] = field(default_factory=list)
    ordered: bool = False
    kind: str = "operation"  # operation | query (display only)

    def signature(self) -> str:
        ps = ", ".join(f":{k} {v}" for k, v in self.params.items())
        return f"{self.name}({ps})"

    def result_text(self) -> str:
        cols = ", ".join(self.columns)
        return {
            "one": f"exactly one row with columns: {cols}",
            "rows": f"rows with columns: {cols}" + (" (order matters)" if self.ordered else " (any order)"),
            "value": "a single value (first column of a single row)",
            "none": "nothing (the result is ignored)",
        }[self.returns]


@dataclass
class Spec:
    schema: str
    operations: dict[str, Operation]


def load_spec(path) -> Spec:
    raw = yaml.safe_load(path.read_text()) or {}
    ops = {}
    for name, o in (raw.get("operations") or {}).items():
        ops[name] = Operation(name=name, doc=str(o.get("doc", "")).strip(), params=dict(o.get("params") or {}),
                              returns=o.get("returns", "none"), columns=list(o.get("columns") or []),
                              ordered=bool(o.get("ordered", False)), kind=o.get("kind", "operation"))
    return Spec(schema=raw.get("schema", "designed"), operations=ops)


def convert(value, t: str):
    """Scenario literal -> Python value psycopg adapts to the declared SQL type."""
    if value is None:
        return None
    if t in ("text",):
        return str(value)
    if t in ("int", "bigint"):
        return int(value)
    if t == "numeric":
        return Decimal(str(value))
    if t == "bool":
        return bool(value)
    if t == "date":
        return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value))
    if t == "timestamptz":
        if isinstance(value, dt.datetime):
            return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
        v = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return v if v.tzinfo else v.replace(tzinfo=dt.timezone.utc)
    if t == "jsonb":
        return Jsonb(value)
    if t == "text[]":
        return [str(v) for v in value]
    if t == "int[]":
        return [int(v) for v in value]
    raise ValueError(f"unknown param type {t!r}")


def literal_issue(value, t: str) -> str | None:
    """Lint: does a scenario literal fit the declared type? ($refs are skipped)."""
    if isinstance(value, str) and value.startswith("$"):
        return None
    if value is None:
        return None
    if isinstance(value, list) and t.endswith("[]"):
        value = [v for v in value if not (isinstance(v, str) and v.startswith("$"))]
    try:
        if t in ("int", "bigint") and (isinstance(value, bool) or not isinstance(value, int)):
            return f"expected {t}, got {value!r}"
        if t == "text" and not isinstance(value, str):
            return f"expected text, YAML gave {value!r} (quote it)"
        if t == "bool" and not isinstance(value, bool):
            return f"expected bool, got {value!r}"
        convert(value, t)
    except (ValueError, TypeError, ArithmeticError) as e:
        return f"{t}: {e}"
    return None


def op_stub(op: Operation) -> str:
    params = "\n".join(f"--   :{k}  ({v})" for k, v in op.params.items()) or "--   (none)"
    doc = "\n".join(f"-- {line}" for line in op.doc.splitlines())
    return (f"-- {op.signature()}\n{doc}\n--\n-- Parameters:\n{params}\n-- Returns: {op.result_text()}\n"
            + ("-- To refuse, raise an error (e.g. via a constraint) or return no row.\n" if op.returns == "one" else "")
            + "--\n-- Runs atomically as its own transaction: no BEGIN/COMMIT.\n"
            "-- Several statements are fine; the last statement's result is the answer.\n\n")


SCHEMA_STUB = """-- Your schema: tables, keys, constraints, indexes.
-- The judge runs this file on an empty PostgreSQL 17 database before every scenario.
-- Enforce the rules here (PRIMARY KEY, UNIQUE, FOREIGN KEY, CHECK, NOT NULL, EXCLUDE ...):
-- the tests expect the DATABASE to reject invalid data, not just your queries.

"""
