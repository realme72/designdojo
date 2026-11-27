"""SQL text helpers: `:name` parameters, comment stripping, transaction-control detection.

A tiny scanner that understands quotes, quoted identifiers, dollar quoting and comments, so a
`:name` inside a string or a `::type` cast is never mistaken for a parameter.
"""

from __future__ import annotations

import re

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_DOLLAR = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)?\$")


def _segments(sql: str):
    """Yield (kind, text) where kind is code | string | ident | comment | dollar."""
    i, n, start = 0, len(sql), 0
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if ch == "-" and nxt == "-":
            j = sql.find("\n", i)
            j = n if j < 0 else j
            kind = "comment"
        elif ch == "/" and nxt == "*":
            j = sql.find("*/", i + 2)
            j = n if j < 0 else j + 2
            kind = "comment"
        elif ch in ("'", '"'):
            j = i + 1
            while j < n:
                if sql[j] == ch:
                    if j + 1 < n and sql[j + 1] == ch:  # doubled quote escape
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            kind = "string" if ch == "'" else "ident"
        elif ch == "$" and (m := _DOLLAR.match(sql, i)) and not (i and (sql[i - 1].isalnum() or sql[i - 1] == "_")):
            tag = m.group(0)
            end = sql.find(tag, m.end())
            j = n if end < 0 else end + len(tag)
            kind = "dollar"
        else:
            i += 1
            continue
        if start < i:
            yield "code", sql[start:i]
        yield kind, sql[i:j]
        i = start = j
    if start < n:
        yield "code", sql[start:]


def param_names(sql: str) -> list[str]:
    names: list[str] = []
    for kind, text in _segments(sql):
        if kind == "code":
            for m in re.finditer(r"(?<![:\w]):([A-Za-z_]\w*)", text):
                if m.group(1) not in names:
                    names.append(m.group(1))
    return names


def to_pyformat(sql: str) -> str:
    """`:name` -> `%(name)s`, and literal `%` in code -> `%%` (psycopg client-side binding)."""
    out = []
    for kind, text in _segments(sql):
        if kind == "code":
            text = text.replace("%", "%%")
            text = re.sub(r"(?<![:\w]):([A-Za-z_]\w*)", r"%(\1)s", text)
        else:
            text = text.replace("%", "%%")
        out.append(text)
    return "".join(out)


def strip_comments(sql: str) -> str:
    return "".join(t for k, t in _segments(sql) if k != "comment")


def is_blank(sql: str) -> bool:
    return not strip_comments(sql).strip().strip(";").strip()


TXN = re.compile(r"(^|;)\s*(begin|commit|rollback|start\s+transaction|end|savepoint|release|abort)\b", re.I)


def transaction_control(sql: str) -> str | None:
    code = "".join(t if k == "code" else " " * len(t) for k, t in _segments(sql))
    m = TXN.search(code)
    return m.group(2).upper() if m else None


def line_of(sql: str, offset: int) -> int:
    """1-based line for a 0-based character offset."""
    return sql.count("\n", 0, max(0, offset)) + 1
