"""Turn Postgres EXPLAIN (FORMAT JSON) output into something a learner can read:
a simplified tree, a bottom-up Mermaid flow (data flows from table scans up to the result),
the logical clause order of the SQL text, and plain-English insights."""

from __future__ import annotations

import re

from .params import strip_comments

COND_KEYS = ("Hash Cond", "Merge Cond", "Index Cond", "Recheck Cond", "Join Filter", "Filter", "One-Time Filter")

EXPLAIN_NODE = {
    "Seq Scan": "Reads every row of the table, in storage order, and checks each one.",
    "Index Scan": "Walks an index to find matching rows, then fetches each row from the table.",
    "Index Only Scan": "Answers from the index alone, without touching the table.",
    "Bitmap Heap Scan": "Fetches the table pages an index said contain matches, in page order.",
    "Bitmap Index Scan": "Collects matching row locations from an index into a bitmap.",
    "Nested Loop": "For each row from the outer input, looks up matching rows in the inner input.",
    "Hash Join": "Builds a hash table from one input, then probes it with every row of the other.",
    "Merge Join": "Walks two inputs sorted on the join key side by side.",
    "Hash": "Builds the in-memory hash table a Hash Join probes.",
    "Sort": "Sorts its input (for ORDER BY, merge joins, or grouping).",
    "Incremental Sort": "Sorts input that is already partly in order, one group at a time.",
    "Aggregate": "Computes aggregates (count, sum, ...) over its input.",
    "HashAggregate": "Groups rows with a hash table and computes aggregates per group.",
    "GroupAggregate": "Groups rows that arrive sorted by the group key.",
    "Limit": "Stops after the first N rows.",
    "Unique": "Removes adjacent duplicate rows (DISTINCT on sorted input).",
    "WindowAgg": "Computes window functions (rank, lag, running sums) over partitions.",
    "CTE Scan": "Reads the rows produced by a WITH query.",
    "Subquery Scan": "Reads the rows of a subquery in FROM.",
    "Materialize": "Keeps its input's rows in memory so they can be re-read cheaply.",
    "Memoize": "Caches inner-side results by key, so repeated lookups are free.",
    "Append": "Concatenates the outputs of its inputs (UNION ALL, partitions).",
    "Result": "Produces a computed row (constants, or a gate on a one-time condition).",
    "ModifyTable": "Inserts, updates or deletes the rows it receives.",
    "ProjectSet": "Expands set-returning functions (e.g. jsonb_array_elements) into rows.",
    "Function Scan": "Reads rows produced by a function (e.g. generate_series, jsonb_array_elements).",
    "Values Scan": "Reads rows from a VALUES list.",
    "Recursive Union": "Runs a recursive CTE: the base query, then repeats the recursive part until no new rows.",
    "WorkTable Scan": "Reads the rows produced by the previous step of a recursive CTE.",
    "Gather": "Collects rows from parallel workers.",
}

CLAUSES = [
    ("WITH", r"^\s*with\b"), ("FROM", r"\bfrom\b"), ("JOIN", r"\bjoin\b"), ("WHERE", r"\bwhere\b"),
    ("GROUP BY", r"\bgroup\s+by\b"), ("HAVING", r"\bhaving\b"), ("WINDOW", r"\bover\s*\("),
    ("SELECT", r"\bselect\b"), ("DISTINCT", r"\bselect\s+distinct\b"), ("ORDER BY", r"\border\s+by\b"),
    ("LIMIT", r"\blimit\b|\bfetch\s+first\b"),
]
CLAUSE_HELP = {
    "WITH": "Named subqueries (CTEs) are defined first; later steps can read them like tables.",
    "FROM": "Pick the source table(s): everything starts here.",
    "JOIN": "Combine rows of the sources wherever the ON condition holds.",
    "WHERE": "Drop rows that don't match, before any grouping.",
    "GROUP BY": "Collapse the remaining rows into one row per group.",
    "HAVING": "Drop groups that don't match (it filters groups, WHERE filters rows).",
    "WINDOW": "Window functions run after grouping, over the surviving rows, without collapsing them.",
    "SELECT": "Compute the output columns (aliases defined here aren't visible to WHERE).",
    "DISTINCT": "Remove duplicate output rows.",
    "ORDER BY": "Sort the output (aliases from SELECT are visible here).",
    "LIMIT": "Keep only the first N rows.",
}


def clauses(sql: str) -> list[dict]:
    code = re.sub(r"'(?:[^']|'')*'", "''", strip_comments(sql)).lower()
    return [{"clause": name, "used": bool(re.search(rx, code, re.S)), "help": CLAUSE_HELP[name]}
            for name, rx in CLAUSES]


def _label(n: dict) -> str:
    t = n.get("Node Type", "?")
    if t == "Aggregate" and n.get("Strategy") in ("Hashed", "Sorted"):
        t = "HashAggregate" if n["Strategy"] == "Hashed" else "GroupAggregate"
    if t == "ModifyTable":
        t = f"{n.get('Operation', 'Modify')} {n.get('Relation Name', '')}".strip()
    return t


def simplify(n: dict, counter: list[int] | None = None) -> dict:
    counter = counter if counter is not None else [0]
    counter[0] += 1
    t = _label(n)
    node = {
        "id": f"n{counter[0]}",
        "type": t,
        "base": n.get("Node Type", "?"),
        "relation": n.get("Relation Name"),
        "alias": n.get("Alias") if n.get("Alias") != n.get("Relation Name") else None,
        "index": n.get("Index Name"),
        "join": n.get("Join Type"),
        "cte": n.get("CTE Name"),
        "conds": {k: n[k] for k in COND_KEYS if k in n},
        "sort_key": n.get("Sort Key"),
        "group_key": n.get("Group Key"),
        "est_rows": n.get("Plan Rows"),
        "rows": n.get("Actual Rows"),
        "loops": n.get("Actual Loops"),
        "ms": n.get("Actual Total Time"),
        "removed": n.get("Rows Removed by Filter", 0) + n.get("Rows Removed by Join Filter", 0),
        "sort_method": n.get("Sort Method"),
        "parent_rel": n.get("Parent Relationship"),
        "subplan": n.get("Subplan Name"),
        "explain": EXPLAIN_NODE.get(n.get("Node Type", ""), ""),
        "children": [],
    }
    node["children"] = [simplify(c, counter) for c in n.get("Plans", [])]
    return node


def _walk(node):
    yield node
    for c in node["children"]:
        yield from _walk(c)


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace('"', "#quot;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("[", "#91;").replace("]", "#93;").replace("{", "#123;").replace("}", "#125;"))


def _short(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def to_mermaid(root: dict, analyzed: bool) -> str:
    lines = ["flowchart BT"]
    for node in _walk(root):
        title = node["type"]
        if node["relation"]:
            title += f" on {node['relation']}" + (f" {node['alias']}" if node["alias"] else "")
        elif node["cte"]:
            title += f" {node['cte']}"
        if node["join"] and "Join" in node["type"] or node["type"] == "Nested Loop":
            title = f"{node['join']} {title}" if node["join"] else title
        parts = [f"<b>{_esc(title)}</b>"]
        if node["index"]:
            parts.append(_esc(f"using {node['index']}"))
        for k, v in node["conds"].items():
            parts.append(_esc(_short(f"{k.lower()}: {v}")))
        if node["sort_key"]:
            parts.append(_esc(_short("by " + ", ".join(node["sort_key"]))))
        if node["group_key"]:
            parts.append(_esc(_short("group by " + ", ".join(node["group_key"]))))
        if analyzed and node["rows"] is not None:
            stat = f"{node['rows']} row" + ("" if node["rows"] == 1 else "s")
            if node["loops"] and node["loops"] > 1:
                stat += f" × {node['loops']} loops"
            if node["removed"]:
                stat += f", {node['removed']} filtered out"
            parts.append(_esc(stat))
        else:
            parts.append(_esc(f"~{node['est_rows']} row(s) estimated"))
        lines.append(f'  {node["id"]}["{"<br/>".join(parts)}"]')
    for node in _walk(root):
        for c in node["children"]:
            n_rows = c["rows"] if analyzed and c["rows"] is not None else c["est_rows"]
            loops = c["loops"] or 1
            count = n_rows * loops if analyzed else n_rows
            label = f"{count} row" + ("" if count == 1 else "s")
            if c["parent_rel"] == "InitPlan" or c["subplan"]:
                label = (c["subplan"] or "subplan") + f" · {label}"
            lines.append(f'  {c["id"]} -->|"{_esc(label)}"| {node["id"]}')
    lines.append(f'  {root["id"]} --> OUT(["result"])')
    return "\n".join(lines)


INDEXES_SQL = """
select c.relname, i.relname, (select json_agg(a.attname order by x.ord)
  from unnest(ix.indkey::int2[]) with ordinality x(n, ord)
  join pg_attribute a on a.attrelid = ix.indrelid and a.attnum = x.n)
from pg_index ix join pg_class c on c.oid = ix.indrelid join pg_class i on i.oid = ix.indexrelid
join pg_namespace n on n.oid = c.relnamespace where n.nspname not in ('pg_catalog', 'information_schema')
"""


def load_indexes(cur) -> dict[str, list[tuple[str, list[str]]]]:
    """table -> [(index name, columns)] so insights can tell 'add an index' from 'it exists'."""
    cur.execute(INDEXES_SQL)
    out: dict[str, list[tuple[str, list[str]]]] = {}
    for table, index, cols in cur.fetchall():
        out.setdefault(table, []).append((index, cols or []))
    return out


def insights(root: dict, analyzed: bool, indexes: dict | None = None) -> list[dict]:
    indexes = indexes or {}
    out = []
    for n in _walk(root):
        where = n["relation"] or n["type"]
        if n["base"] == "Seq Scan" and n["conds"].get("Filter"):
            cols = sorted(set(re.findall(r"\(?(\w+)\s*(?:=|<|>|<=|>=|~~)", n["conds"]["Filter"])))
            scanned = (n["rows"] or 0) + n["removed"] if analyzed else None
            msg = f"Reads all of {where} and filters on {n['conds']['Filter']}"
            if analyzed and scanned:
                msg += f": {scanned} row(s) read to keep {n['rows']}"
            existing = next((name for name, icols in indexes.get(n["relation"] or "", [])
                             if icols and icols[0] in cols), None)
            if existing:
                msg += (f". An index that can serve this exists ({existing}); with this little data a full scan "
                        "is cheaper, so Postgres skips it. With real volume it would use the index.")
            else:
                msg += (". Fine for tiny tables; at scale an index on "
                        f"{where}({', '.join(cols) or 'the filtered column'}) lets Postgres jump straight to matches.")
            out.append({"level": "info", "node": n["id"], "text": msg})
        if analyzed and n["loops"] and n["loops"] > 5 and n["base"] in ("Seq Scan", "Index Scan", "Index Only Scan"):
            out.append({"level": "warning", "node": n["id"],
                        "text": f"{where} is scanned {n['loops']} times (once per outer row): a nested loop "
                                "or correlated subquery. A join or an index on the lookup column avoids repeats."})
        if n["subplan"] and analyzed and (n["loops"] or 0) > 1:
            out.append({"level": "warning", "node": n["id"],
                        "text": f"{n['subplan']} runs {n['loops']} times, once per row: a correlated subquery. "
                                "Consider rewriting it as a JOIN or a window function."})
        if analyzed and n["rows"] is not None and n["est_rows"]:
            actual, est = max(n["rows"], 1), max(n["est_rows"], 1)
            if max(actual / est, est / actual) >= 10 and max(actual, est) >= 50:
                out.append({"level": "info", "node": n["id"],
                            "text": f"{n['type']} expected ~{n['est_rows']} rows but got {n['rows']}: stale "
                                    "statistics (run ANALYZE) or a condition the planner can't estimate."})
        if n["sort_method"] and "external" in n["sort_method"].lower():
            out.append({"level": "warning", "node": n["id"],
                        "text": "The sort spilled to disk (external merge): too many rows for work_mem."})
        if n["base"] in ("Nested Loop",) and not any(c["base"].startswith("Index") for c in _walk(n)) \
                and not n["conds"] and analyzed and (n["rows"] or 0) > 20:
            out.append({"level": "warning", "node": n["id"],
                        "text": "Nested loop without a join condition on an index: check for a missing or "
                                "wrong ON clause (accidental cross join)."})
    return out


def describe_plan(plan_json, sql: str, analyzed: bool, indexes: dict | None = None) -> dict:
    top = plan_json[0] if isinstance(plan_json, list) else plan_json
    root = simplify(top["Plan"])
    return {
        "analyzed": analyzed,
        "tree": root,
        "mermaid": to_mermaid(root, analyzed),
        "insights": insights(root, analyzed, indexes),
        "clauses": clauses(sql),
        "planning_ms": top.get("Planning Time"),
        "execution_ms": top.get("Execution Time"),
    }


def single_statement(sql: str) -> str | None:
    """The statement if `sql` holds exactly one, else None (EXPLAIN takes one statement)."""
    from .params import _segments

    parts, buf = [], []
    for kind, text in _segments(sql):
        if kind == "code" and ";" in text:
            pieces = text.split(";")
            buf.append(pieces[0])
            for p in pieces[1:]:
                parts.append("".join(buf))
                buf = [p]
        else:
            buf.append(text)
    parts.append("".join(buf))
    real = [p for p in parts if strip_comments(p).strip()]
    return strip_comments(real[0]).strip() if len(real) == 1 else None


READ_ONLY = re.compile(r"^\s*(with\b(?!.*\b(insert|update|delete|merge)\b)|select\b|values\b|table\b)", re.I | re.S)


def is_read_only(sql: str) -> bool:
    return bool(READ_ONLY.match(strip_comments(sql)))
