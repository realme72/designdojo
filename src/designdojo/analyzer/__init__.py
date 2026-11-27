"""Static analysis of a workspace's solution: class graph, smells, class diagram.

Pure parsing (tree-sitter): user code is never executed here, so it runs on the host.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from . import java, python
from .detectors import detect
from .diagram import to_mermaid
from .model import SMELLS, ClassInfo, Smell

EXT = {"java": ".java", "python": ".py"}
PARSERS = {"java": java.parse_file, "python": python.parse_file}
MAX_FILES = 200

__all__ = ["analyze", "SMELLS"]


def analyze(root: Path, lang: str, *, concurrency: bool = False, contract_types: set[str] | None = None) -> dict:
    """Analyze <root>/solution. Paths in the result are relative to root (e.g. solution/Lot.java)."""
    if lang == "sql":
        from ..sql.analyze import analyze_workspace

        return analyze_workspace(root)
    contract_types = contract_types or set()
    classes: list[ClassInfo] = []
    smells: list[Smell] = []
    lines = 0
    files = sorted((root / "solution").rglob(f"*{EXT[lang]}"))[:MAX_FILES]
    for path in files:
        src = path.read_bytes()
        lines += src.count(b"\n")
        c, s = PARSERS[lang](src, path.relative_to(root).as_posix())
        classes += c
        smells += s

    abstractions = {c.name for c in classes if c.is_abstraction} | contract_types
    if lang == "python":
        # Python has no `implements`: a base that is an abstraction is an interface edge.
        for c in classes:
            c.implements = [b for b in c.extends if b in abstractions]
            c.extends = [b for b in c.extends if b not in abstractions]

    smells += detect(classes, concurrency)
    smells.sort(key=lambda s: (s.level != "warning", s.file, s.line_start, s.id))

    def cls_json(c: ClassInfo) -> dict:
        d = asdict(c)
        for m in d["methods"]:
            for k in ("reads", "writes", "mutates", "branches_on", "assigns_const", "calls_self"):
                m[k] = sorted(m[k])
        return d

    return {
        "lang": lang,
        "classes": [cls_json(c) for c in classes],
        "smells": [s.to_json() for s in smells],
        "mermaid": to_mermaid(classes, contract_types),
        "stats": {
            "files": len(files),
            "lines": lines,
            "classes": sum(1 for c in classes if not c.is_abstraction),
            "abstractions": sum(1 for c in classes if c.is_abstraction),
            "methods": sum(len(c.methods) for c in classes),
        },
    }
