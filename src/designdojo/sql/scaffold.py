"""Workspace layout for SQL problems.

    solution/schema.sql          (designed-schema problems)
    solution/ops/<name>.sql      one file per operation / query
    contract/schema.sql          (query drills: the given schema, read-only)
    contract/operations.md       what each operation takes and returns (read-only)
"""

from __future__ import annotations

from pathlib import Path

from .spec import SCHEMA_STUB, Spec, op_stub


def operations_doc(spec: Spec) -> str:
    out = ["# Operations\n", "Implement each one in `solution/ops/<name>.sql`. Use `:param` placeholders.\n"]
    for op in spec.operations.values():
        out.append(f"## {op.signature()}\n\n{op.doc}\n\nReturns {op.result_text()}.\n")
    return "\n".join(out)


def contract_files(problem, spec: Spec) -> dict[str, str]:
    files = {"contract/operations.sql": "-- (reference) " + "\n-- ".join(operations_doc(spec).splitlines()) + "\n"}
    if spec.schema == "provided":
        files["contract/schema.sql"] = (problem.root / "schema.sql").read_text()
    return files


def stub_files(spec: Spec) -> dict[str, str]:
    files = {f"solution/ops/{name}.sql": op_stub(op) for name, op in spec.operations.items()}
    if spec.schema == "designed":
        files["solution/schema.sql"] = SCHEMA_STUB
    return files


def entry_file(spec: Spec) -> str:
    return "solution/schema.sql" if spec.schema == "designed" else f"solution/ops/{next(iter(spec.operations))}.sql"


def schema_source(ws) -> tuple[str, str]:
    """(display path, sql) of the schema the judge applies."""
    spec = ws.problem.sql_spec
    if spec.schema == "provided":
        return "contract/schema.sql", (ws.problem.root / "schema.sql").read_text()
    p = Path(ws.root) / "solution" / "schema.sql"
    return "solution/schema.sql", p.read_text() if p.exists() else ""
