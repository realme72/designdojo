"""Model -> Mermaid classDiagram."""

from __future__ import annotations

import re

from .detectors import base_type
from .model import ClassInfo

COLLECTIONS = {"List", "Set", "Map", "Collection", "Queue", "Deque", "NavigableSet", "SortedSet", "Iterable",
               "list", "set", "dict", "deque", "tuple", "frozenset", "defaultdict", "Sequence", "Mapping"}
STEREOTYPE = {"interface": "interface", "abstract": "abstract", "enum": "enumeration", "record": "record",
              "dataclass": "dataclass", "exception": "exception"}
MAX_FIELDS = 8
MAX_METHODS = 10


def _ident(name: str) -> str:
    return re.sub(r"\W", "_", name)


def _type_label(t: str | None) -> str:
    if not t:
        return ""
    # Mermaid generics use ~T~; keep one level and drop the rest for readability.
    t = re.sub(r"\s+", "", t)
    m = re.match(r"^([\w.]+)[<\[](.*)[>\]]$", t)
    if m:
        inner = ",".join(base_type(x) for x in re.split(r",(?![^<\[]*[>\]])", m.group(2)))
        return f"{base_type(m.group(1))}~{inner}~"
    return base_type(t)


def to_mermaid(classes: list[ClassInfo], contract_types: set[str]) -> str:
    local = {c.name for c in classes}
    lines = ["classDiagram", "  direction LR"]
    externals: set[str] = set()
    edges: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()

    for c in classes:
        cid = _ident(c.name)
        lines.append(f"  class {cid} {{")
        if c.kind in STEREOTYPE:
            lines.append(f"    <<{STEREOTYPE[c.kind]}>>")
        for f in [f for f in c.fields if not f.static][:MAX_FIELDS]:
            if c.kind == "enum":
                lines.append(f"    {f.name}")
            else:
                label = _type_label(f.type)
                lines.append(f"    -{f.name}{': ' + label if label else ''}" if label else f"    -{f.name}")
        shown = [m for m in c.methods if not m.ctor and not m.private and not m.name.startswith("__")]
        for m in shown[:MAX_METHODS]:
            lines.append(f"    +{m.name}({', '.join(m.params)}){'*' if m.abstract else ''}")
        lines.append("  }")

        for parent in c.extends:
            if parent in local or parent in contract_types:
                edges.append(f"  {_ident(parent)} <|-- {cid}")
                if parent not in local:
                    externals.add(parent)
        for iface in c.implements:
            if iface in local or iface in contract_types:
                edges.append(f"  {_ident(iface)} <|.. {cid}")
                if iface not in local:
                    externals.add(iface)

        for f in c.fields:
            if f.static or not f.type:
                continue
            names = re.findall(r"[A-Za-z_]\w*", f.type)
            many = any(n in COLLECTIONS for n in names)
            for n in dict.fromkeys(names):
                if n in local and n != c.name and (c.name, n) not in seen_pairs:
                    seen_pairs.add((c.name, n))
                    mult = ' "*"' if many else ""
                    edges.append(f"  {cid} -->{mult} {_ident(n)} : {f.name}")
        for m in c.methods:
            for t, _ in m.instantiates:
                if t in local and t != c.name and (c.name, t) not in seen_pairs:
                    target = next(x for x in classes if x.name == t)
                    if target.kind == "exception":
                        continue
                    seen_pairs.add((c.name, t))
                    edges.append(f"  {cid} ..> {_ident(t)} : creates")

    for e in sorted(externals):
        lines.append(f"  class {_ident(e)} {{")
        lines.append("    <<contract>>")
        lines.append("  }")
    return "\n".join(lines + edges) + "\n"
