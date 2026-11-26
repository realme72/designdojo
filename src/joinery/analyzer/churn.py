"""Churn between two versions of a solution: how much *existing* code a curveball forced you to edit.

Symbols are methods/functions plus each class's (and Python module's) non-method body, so editing a
field initializer or an enum table counts too. Comparison ignores comments and whitespace. Edits to
the composition root (`create`) are reported as wiring and not penalised: registering a new
strategy there is exactly what Open/Closed expects.

A changed symbol whose only change is *inserted lines with no new branching* (a new table row,
enum entry, `fits.put(...)`) counts as **extended**, not modified: that's how data-driven designs
grow. Inserting an `if`/`elif`/`case`/`switch` branch, or editing existing lines, is **modified**.

extensibility = (added + extended) / (added + extended + 2*modified + 2*deleted); 1.0 if nothing changed.
"""

from __future__ import annotations

import ast
import difflib
import re
from pathlib import Path

from . import java as java_parser

WIRING = {"Solution.create", "__init__:create"}
BRANCH = re.compile(r"\b(if|elif|else|case|switch|when|match|default)\b|\?[^:]*:")


def _norm_java(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return "\n".join(re.sub(r"\s+", " ", l).strip() for l in text.splitlines() if l.strip())


def _change_kind(old: str, new: str) -> str:
    """'extended' for pure insertions without new branching, else 'modified'."""
    ops = difflib.SequenceMatcher(a=old.splitlines(), b=new.splitlines(), autojunk=False).get_opcodes()
    inserted = []
    for tag, _i1, _i2, j1, j2 in ops:
        if tag in ("replace", "delete"):
            return "modified"
        if tag == "insert":
            inserted += new.splitlines()[j1:j2]
    return "modified" if any(BRANCH.search(l) for l in inserted) else "extended"


def _norm_py(text: str) -> str:
    out = []
    for line in text.splitlines():
        line = re.sub(r"#.*$", "", line).strip()
        if line:
            out.append(line)
    return "\n".join(out)


def _java_symbols(root: Path) -> dict[str, str]:
    syms: dict[str, str] = {}
    for path in sorted((root / "solution").rglob("*.java")):
        lines = path.read_text().splitlines()
        classes, _ = java_parser.parse_file(path.read_bytes(), path.name)
        for c in classes:
            body = set()
            for m in c.methods:
                base = f"{c.name}.{'<init>' if m.ctor else m.name}"
                key = base if base in WIRING else f"{base}({len(m.params)})"  # arity: overloads differ
                syms[key] = _norm_java("\n".join(lines[m.line_start - 1:m.line_end]))
                body.update(range(m.line_start, m.line_end + 1))
            rest = [l for i, l in enumerate(lines[c.line_start - 1:c.line_end], c.line_start) if i not in body]
            syms[f"{c.name} (fields)"] = _norm_java("\n".join(rest))
    return syms


def _py_symbols(root: Path) -> dict[str, str]:
    syms: dict[str, str] = {}
    for path in sorted((root / "solution").rglob("*.py")):
        src = path.read_text()
        lines = src.splitlines()
        mod = path.relative_to(root / "solution").with_suffix("").as_posix().replace("/", ".")
        tree = ast.parse(src)

        def seg(node) -> str:
            return "\n".join(lines[node.lineno - 1:node.end_lineno])

        loose = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                syms[f"{mod}:{node.name}"] = _norm_py(seg(node))
            elif isinstance(node, ast.ClassDef):
                rest = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        syms[f"{node.name}.{item.name}"] = _norm_py(seg(item))
                    else:
                        rest.append(seg(item))
                header = lines[node.lineno - 1]
                syms[f"{node.name} (body)"] = _norm_py("\n".join([header, *rest]))
            elif not isinstance(node, (ast.Import, ast.ImportFrom)):
                if not (isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant)):
                    loose.append(seg(node))  # constants, tables, registrations (docstrings skipped)
        if loose:
            syms[f"{mod} (module)"] = _norm_py("\n".join(loose))
    return syms


def symbols(root: Path, lang: str) -> dict[str, str]:
    return _java_symbols(root) if lang == "java" else _py_symbols(root)


def churn(before: Path, after: Path, lang: str) -> dict:
    """before/after are directories containing a `solution/` folder."""
    a, b = symbols(before, lang), symbols(after, lang)
    added = sorted(k for k in b if k not in a and b[k])
    deleted = sorted(k for k in a if k not in b and a[k])
    changed = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
    wiring = [k for k in changed if k in WIRING]
    extended = [k for k in changed if k not in WIRING and _change_kind(a[k], b[k]) == "extended"]
    modified = [k for k in changed if k not in WIRING and k not in extended]
    grew = len(added) + len(extended)
    denom = grew + 2 * len(modified) + 2 * len(deleted)
    score = 1.0 if (not modified and not deleted) else (grew / denom if denom else 1.0)
    return {"added": added, "extended": extended, "modified": modified, "deleted": deleted, "wiring": wiring,
            "extensibility": round(score, 3)}
