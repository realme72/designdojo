"""Static design signals for a schema, read from the Postgres catalog (not by parsing SQL).

The schema is applied inside a transaction on a scratch database and rolled back. Output has
the same shape as the code analyzer (smells, mermaid, stats), plus `tables` for the coach.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import psycopg

from . import pg
from .params import is_blank, strip_comments

SQL_SMELLS = {
    "NO_PRIMARY_KEY": ("Table without a primary key", ["Entity integrity", "Add a PRIMARY KEY"]),
    "MISSING_FK": ("Looks like a reference but has no foreign key", ["Referential integrity", "FOREIGN KEY"]),
    "FK_NOT_INDEXED": ("Foreign key without an index", ["Index FK columns used in joins/deletes"]),
    "FLOAT_MONEY": ("Money stored as a floating-point number", ["numeric(p,s) or integer cents"]),
    "NO_DOMAIN_CHECK": ("Quantity/price column without a CHECK", ["Domain integrity", "CHECK constraint"]),
    "UNCONSTRAINED_STATUS": ("Free-text status/type column", ["CHECK (... IN (...))", "enum type", "lookup table"]),
    "NO_NATURAL_KEY": ("Natural identifier not unique", ["UNIQUE constraint"]),
    "REPEATING_GROUP": ("Repeating group of columns", ["1NF", "Child table"]),
    "SERIAL_TYPE": ("serial instead of an identity column", ["GENERATED ... AS IDENTITY"]),
    "TIMESTAMP_NO_TZ": ("timestamp without time zone", ["timestamptz"]),
    "SELECT_STAR": ("SELECT * in an operation", ["Name the columns you return"]),
    "NOT_IN_SUBQUERY": ("NOT IN (subquery) is NULL-unsafe", ["NOT EXISTS", "LEFT JOIN ... IS NULL"]),
    "COMMA_JOIN": ("Implicit comma join", ["Explicit JOIN ... ON"]),
    "SCHEMA_ERROR": ("Schema does not apply", ["Fix the error first"]),
}

MONEY = re.compile(r"(price|amount|total|balance|cost|fee|salary|revenue|cents|paid|budget)", re.I)
QTY = re.compile(r"^(qty|quantity|stock|capacity|seats|price|amount|unit_price|salary|rating|score|age)$", re.I)
STATUS = re.compile(r"^(status|state|type|kind|role|category|level|tier)$", re.I)
NATURAL = re.compile(r"^(email|username|handle|sku|isbn|slug|code|phone|license_plate|plate)$", re.I)
GROUP = re.compile(r"^(.*?)_?(\d+)$")

CATALOG = """
with t as (
  select c.oid, c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where c.relkind in ('r','p') and n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%'
)
select json_build_object(
 'tables', (select coalesce(json_agg(json_build_object('name', t.relname,
    'columns', (select json_agg(json_build_object('name', a.attname, 'type', format_type(a.atttypid, a.atttypmod),
                 'notnull', a.attnotnull, 'identity', a.attidentity <> '', 'default', pg_get_expr(d.adbin, d.adrelid),
                 'enum', exists(select 1 from pg_enum e where e.enumtypid = a.atttypid),
                 'num', a.attnum) order by a.attnum)
               from pg_attribute a left join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
               where a.attrelid = t.oid and a.attnum > 0 and not a.attisdropped),
    'constraints', (select coalesce(json_agg(json_build_object('name', k.conname, 'type', k.contype,
                 'cols', (select json_agg(a.attname order by x.ord) from unnest(k.conkey) with ordinality x(n, ord)
                          join pg_attribute a on a.attrelid = k.conrelid and a.attnum = x.n),
                 'ref', (select relname from pg_class where oid = k.confrelid),
                 'refcols', (select json_agg(a.attname order by x.ord) from unnest(k.confkey) with ordinality x(n, ord)
                          join pg_attribute a on a.attrelid = k.confrelid and a.attnum = x.n),
                 'def', pg_get_constraintdef(k.oid))), '[]'::json)
               from pg_constraint k where k.conrelid = t.oid),
    'indexes', (select coalesce(json_agg(json_build_object('unique', i.indisunique, 'def', pg_get_indexdef(i.indexrelid),
                 'cols', (select json_agg(a.attname order by x.ord) from unnest(i.indkey::int2[]) with ordinality x(n, ord)
                          join pg_attribute a on a.attrelid = i.indrelid and a.attnum = x.n))), '[]'::json)
               from pg_index i where i.indrelid = t.oid)
  ) order by t.relname), '[]'::json) from t)
)
"""


def _smell(sid, file, line, symbol, evidence, level="warning", line_end=None):
    title, suggests = SQL_SMELLS[sid]
    return {"id": sid, "file": file, "line_start": line, "line_end": line_end or line, "symbol": symbol,
            "evidence": evidence, "level": level, "title": title, "suggests": suggests}


def _table_lines(sql: str) -> dict[str, tuple[int, int]]:
    """Best-effort line span of each CREATE TABLE (for anchoring signals in the editor)."""
    spans = {}
    for m in re.finditer(r"create\s+(?:unlogged\s+)?table\s+(?:if\s+not\s+exists\s+)?(?:\w+\.)?\"?(\w+)\"?",
                         sql, re.I):
        start = sql.count("\n", 0, m.start()) + 1
        end_idx = sql.find(";", m.end())
        end = sql.count("\n", 0, end_idx if end_idx >= 0 else len(sql)) + 1
        spans[m.group(1).lower()] = (start, end)
    return spans


def _column_line(sql: str, span: tuple[int, int], col: str) -> int:
    lines = sql.splitlines()
    for i in range(span[0] - 1, min(span[1], len(lines))):
        if re.search(rf"(^|[\s(,]){re.escape(col)}\b", lines[i], re.I) and i + 1 != span[0]:
            return i + 1
    return span[0]


def _singular(name: str) -> set[str]:
    out = {name}
    if name.endswith("ies"):
        out.add(name[:-3] + "y")
    if name.endswith("es"):
        out.add(name[:-2])
    if name.endswith("s"):
        out.add(name[:-1])
    return out


def schema_smells(catalog: dict, sql: str, file: str) -> list[dict]:
    spans = _table_lines(sql)
    smells = []
    by_singular = {s: t["name"] for t in catalog["tables"] for s in _singular(t["name"])}
    for t in catalog["tables"]:
        name = t["name"]
        span = spans.get(name, (1, 1))
        cons = t["constraints"]
        pk = next((c for c in cons if c["type"] == "p"), None)
        fk_cols = [c["cols"] for c in cons if c["type"] == "f"]
        fk_flat = {col for cols in fk_cols for col in cols}
        unique_sets = ([c["cols"] for c in cons if c["type"] in ("p", "u")]
                       + [i["cols"] or [] for i in t["indexes"] if i["unique"]])
        checks = " ".join(c["def"] for c in cons if c["type"] == "c").lower()
        if not pk:
            smells.append(_smell("NO_PRIMARY_KEY", file, span[0], name, f"{name} has no primary key", line_end=span[1]))
        for cols in fk_cols:
            # covered when an index's leading columns are the FK columns (any order), or it starts with the
            # FK's first column (a composite FK like (tenant_id, user_id) is narrowed well by that prefix)
            indexed = any(set((i["cols"] or [])[: len(cols)]) == set(cols) or (i["cols"] or [None])[0] == cols[0]
                          for i in t["indexes"])
            if not indexed:
                line = _column_line(sql, span, cols[0])
                smells.append(_smell("FK_NOT_INDEXED", file, line, f"{name}.{','.join(cols)}",
                                     f"{name}({', '.join(cols)}) references another table but no index starts "
                                     "with it: joins and parent deletes scan the table", "info"))
        groups: dict[str, list[str]] = {}
        for col in t["columns"]:
            c, typ = col["name"], col["type"]
            line = _column_line(sql, span, c)
            if c.endswith("_id") and c not in fk_flat and not (pk and pk["cols"] == [c]):
                target = by_singular.get(c[:-3]) or by_singular.get(c[:-3] + "s")
                if target:
                    smells.append(_smell("MISSING_FK", file, line, f"{name}.{c}",
                                         f"{name}.{c} looks like it points at {target} but has no FOREIGN KEY"))
            if typ in ("real", "double precision") and MONEY.search(c):
                smells.append(_smell("FLOAT_MONEY", file, line, f"{name}.{c}",
                                     f"{name}.{c} is {typ}: binary floating point can't represent 0.10 exactly"))
            if QTY.match(c) and c not in checks and not col["enum"] and c not in fk_flat:
                smells.append(_smell("NO_DOMAIN_CHECK", file, line, f"{name}.{c}",
                                     f"{name}.{c} accepts negative/zero values; nothing CHECKs its range", "info"))
            in_key = any(c in u for u in unique_sets)
            if (STATUS.match(c) and typ.startswith(("text", "character")) and not col["enum"]
                    and c not in checks and c not in fk_flat and not in_key):
                smells.append(_smell("UNCONSTRAINED_STATUS", file, line, f"{name}.{c}",
                                     f"{name}.{c} is free text: any typo becomes a new state", "info"))
            expr_unique = any(i["unique"] and not i["cols"] and re.search(rf"\b{c}\b", i["def"]) for i in t["indexes"])
            if NATURAL.match(c) and not expr_unique and not in_key:
                smells.append(_smell("NO_NATURAL_KEY", file, line, f"{name}.{c}",
                                     f"{name}.{c} isn't UNIQUE: two rows can claim the same {c}", "info"))
            if col["default"] and "nextval(" in col["default"]:
                smells.append(_smell("SERIAL_TYPE", file, line, f"{name}.{c}",
                                     f"{name}.{c} uses serial; GENERATED ... AS IDENTITY is the SQL-standard form",
                                     "info"))
            if typ == "timestamp without time zone":
                smells.append(_smell("TIMESTAMP_NO_TZ", file, line, f"{name}.{c}",
                                     f"{name}.{c} has no time zone: instants become ambiguous across zones", "info"))
            if (m := GROUP.match(c)) and m.group(1):
                groups.setdefault(m.group(1), []).append(c)
        for base, cols in groups.items():
            if len(cols) >= 2:
                line = _column_line(sql, span, cols[0])
                smells.append(_smell("REPEATING_GROUP", file, line, f"{name}.{base}",
                                     f"{name} has {', '.join(cols)}: a list squeezed into columns (1NF)"))
    return smells


def query_smells(files: dict[str, str]) -> list[dict]:
    out = []
    for path, src in files.items():
        if not path.startswith("solution/ops/"):
            continue
        code = strip_comments(src)
        lines = src.splitlines()

        def line_for(pattern):
            for i, ln in enumerate(lines, 1):
                if not ln.lstrip().startswith("--") and re.search(pattern, ln, re.I):
                    return i
            return 1

        if re.search(r"select\s+(\w+\.)?\*", code, re.I) and not re.search(r"count\s*\(\s*\*", code, re.I):
            out.append(_smell("SELECT_STAR", path, line_for(r"select\s+(\w+\.)?\*"), path,
                              "SELECT * couples the result to the table layout", "info"))
        if re.search(r"not\s+in\s*\(\s*select", code, re.I):
            out.append(_smell("NOT_IN_SUBQUERY", path, line_for(r"not\s+in"), path,
                              "if the subquery returns a NULL, NOT IN matches nothing"))
        ctes = {m.lower() for m in re.findall(r"(\w+)\s+as\s*(?:not\s+)?(?:materialized\s+)?\(", code, re.I)}
        def real_comma_join(m):
            first, second, call = m.group(1).lower(), m.group(3).lower(), m.group(4)
            return not call and first not in ctes and second not in ctes
        if any(real_comma_join(m) for m in
               re.finditer(r"\bfrom\s+(\w+)(\s+\w+)?\s*,\s*(\w+)(\s*\()?", code, re.I)):
            out.append(_smell("COMMA_JOIN", path, line_for(r"\bfrom\s+\w+(\s+\w+)?\s*,"), path,
                              "FROM a, b with the join condition in WHERE: easy to turn into a cross join", "info"))
    return out


def _type_token(t: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", t).strip("_") or "type"


def to_mermaid(catalog: dict) -> str:
    lines = ["erDiagram"]
    for t in catalog["tables"]:
        cons = t["constraints"]
        pk = {c for k in cons if k["type"] == "p" for c in k["cols"]}
        fk = {c for k in cons if k["type"] == "f" for c in k["cols"]}
        uk = {k["cols"][0] for k in cons if k["type"] == "u" and len(k["cols"]) == 1}
        lines.append(f"  {t['name']} {{")
        for col in t["columns"]:
            keys = [k for k, s in (("PK", pk), ("FK", fk), ("UK", uk)) if col["name"] in s]
            lines.append(f"    {_type_token(col['type'])} {col['name']}" + (f" {', '.join(keys)}" if keys else ""))
        lines.append("  }")
    for t in catalog["tables"]:
        cols = {c["name"]: c for c in t["columns"]}
        uniques = [k["cols"] for k in t["constraints"] if k["type"] in ("p", "u")]
        for k in t["constraints"]:
            if k["type"] != "f" or not k["ref"]:
                continue
            optional = any(not cols[c]["notnull"] for c in k["cols"])
            one_to_one = any(set(u) <= set(k["cols"]) for u in uniques)
            parent = "|o" if optional else "||"
            child = "o|" if one_to_one else "o{"
            lines.append(f'  {k["ref"]} {parent}--{child} {t["name"]} : "{", ".join(k["cols"])}"')
    if len(lines) == 1:
        lines.append("  NO_TABLES_YET { text create_your_tables }")
    return "\n".join(lines)


def graph_text(catalog: dict) -> str:
    out = []
    for t in catalog["tables"]:
        cols = ", ".join(f"{c['name']} {c['type']}{' NOT NULL' if c['notnull'] else ''}" for c in t["columns"])
        cons = "; ".join(c["def"] for c in t["constraints"])
        idx = "; ".join(("unique " if i["unique"] else "") + f"({', '.join(i['cols'] or [])})" for i in t["indexes"])
        out.append(f"- {t['name']}: {cols}\n  constraints: {cons or '-'}\n  indexes: {idx or '-'}")
    return "\n".join(out) or "- no tables"


_cache: dict[str, dict] = {}
_last_good: dict[str, dict] = {}  # workspace -> last catalog that applied (shown while the schema is broken)


def load_catalog(schema_sql: str) -> dict:
    key = hashlib.sha256(schema_sql.encode()).hexdigest()
    if key in _cache:
        return _cache[key]
    with pg.job_database() as dsn, pg.connect(dsn) as conn:
        try:
            cur = conn.cursor()
            cur.execute(schema_sql)
            cur.execute(CATALOG)
            catalog = cur.fetchone()[0]
        finally:
            conn.rollback()
    _cache[key] = catalog
    return catalog


def analyze_workspace(root: Path) -> dict:
    root = Path(root)
    designed = root / "solution" / "schema.sql"
    schema_file = designed if designed.exists() else root / "contract" / "schema.sql"
    rel = schema_file.relative_to(root).as_posix()
    sql = schema_file.read_text() if schema_file.exists() else ""
    files = {p.relative_to(root).as_posix(): p.read_text() for p in sorted((root / "solution").rglob("*.sql"))}
    smells: list[dict] = []
    catalog = {"tables": []}
    if not is_blank(sql):
        try:
            catalog = load_catalog(sql)
            _last_good[str(root)] = catalog
        except psycopg.Error as e:
            catalog = _last_good.get(str(root), catalog)
            from .judge import _schema_diagnostic

            d = _schema_diagnostic(rel, sql, e)
            smells.append(_smell("SCHEMA_ERROR", rel, max(1, d["line"]), rel, d["message"]))
    if rel.startswith("solution/") and not smells:  # no design signals for a schema that doesn't apply
        smells += schema_smells(catalog, sql, rel)
    smells += query_smells(files)
    smells.sort(key=lambda s: (s["level"] != "warning", s["file"], s["line_start"], s["id"]))
    fks = sum(1 for t in catalog["tables"] for c in t["constraints"] if c["type"] == "f")
    checks = sum(1 for t in catalog["tables"] for c in t["constraints"] if c["type"] in ("c", "x", "u"))
    return {
        "lang": "sql",
        "classes": [],
        "smells": smells,
        "mermaid": to_mermaid(catalog),
        "graph_text": graph_text(catalog),
        "tables": catalog["tables"],
        "stats": {"files": len(files), "lines": sum(s.count("\n") for s in files.values()),
                  "tables": len(catalog["tables"]), "relationships": fks, "constraints": checks,
                  "classes": len(catalog["tables"]), "abstractions": fks, "methods": checks},
    }


if __name__ == "__main__":  # debugging aid: python -m designdojo.sql.analyze <workspace>
    import sys

    print(json.dumps(analyze_workspace(Path(sys.argv[1])), indent=2)[:4000])
