"""Smells computed from the language-neutral model (both languages share these)."""

from __future__ import annotations

import re

from .model import UNSAFE_MUTABLE_TYPES, ClassInfo, Method, Smell

GOD_METHODS = 10
GOD_FIELDS = 8
LCOM_MIN_METHODS = 6
LCOM_COMPONENTS = 3
CTOR_PARAMS = 6
FAT_INTERFACE_METHODS = 7
FACTORY_NAMES = re.compile(r"^(create|build|make|of|from|new|newInstance|valueOf|copy)\w*$", re.I)
COMPOSITION_ROOTS = {"Solution"}
COUNTER_TYPES = {"int", "long", "short", "Integer", "Long", "Short"}
THREAD_SAFE_HINTS = ("Concurrent", "Atomic", "synchronized", "CopyOnWrite", "Blocking", "Lock", "queue.Queue")


def base_type(t: str | None) -> str:
    if not t:
        return ""
    return re.split(r"[<\[(]", t.strip())[0].split(".")[-1]


def lcom4(methods: list[Method]) -> int:
    """Connected components of methods linked by shared fields or calls. 1 = cohesive."""
    names = [m.name for m in methods]
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for i, a in enumerate(methods):
        for b in methods[i + 1:]:
            if a.touched & b.touched:
                union(a.name, b.name)
        for callee in a.calls_self:
            if callee in parent:
                union(a.name, callee)
    return len({find(n) for n in names})


def detect(classes: list[ClassInfo], concurrency: bool) -> list[Smell]:
    smells: list[Smell] = []
    collaborators = {
        c.name for c in classes
        if not c.is_value and not c.is_abstraction and c.name not in COMPOSITION_ROOTS
        and any(not m.ctor for m in c.methods)
    }

    for c in classes:
        inst = [m for m in c.methods if not m.ctor and not m.static]
        inst_fields = [f for f in c.fields if not f.static]

        if not c.is_value and not c.is_abstraction:
            comps = lcom4(inst) if inst else 0
            reasons = []
            if len(inst) >= GOD_METHODS:
                reasons.append(f"{len(inst)} methods")
            if len(inst_fields) >= GOD_FIELDS:
                reasons.append(f"{len(inst_fields)} fields")
            if len(inst) >= LCOM_MIN_METHODS and comps >= LCOM_COMPONENTS:
                reasons.append(f"methods split into {comps} groups that share no fields")
            if reasons:
                smells.append(Smell("GOD_CLASS", c.file, c.line_start, c.line_end, c.name,
                                    f"`{c.name}`: " + ", ".join(reasons)))

        if c.kind not in ("record", "dataclass"):
            for m in c.methods:
                if m.ctor and len(m.params) >= CTOR_PARAMS:
                    smells.append(Smell("TELESCOPING_CTOR", c.file, m.line_start, m.line_start, c.name,
                                        f"constructor takes {len(m.params)} parameters"))

        if c.is_abstraction:
            abstract = [m for m in c.methods if m.abstract]
            if len(abstract) >= FAT_INTERFACE_METHODS:
                smells.append(Smell("FAT_INTERFACE", c.file, c.line_start, c.line_end, c.name,
                                    f"`{c.name}` declares {len(abstract)} abstract methods"))
            impls = [x.name for x in classes if c.name in x.implements or c.name in x.extends]
            if len(impls) == 1:
                smells.append(Smell("SPECULATIVE_PATTERN", c.file, c.line_start, c.line_start, c.name,
                                    f"`{c.name}` has one implementation ({impls[0]}). Fine if a second is "
                                    f"plausible; otherwise it's indirection", "info"))

        if c.name not in COMPOSITION_ROOTS:
            for m in c.methods:
                if m.ctor or FACTORY_NAMES.match(m.name):
                    continue
                made = sorted({t for t, _ in m.instantiates if t in collaborators and t != c.name})
                if made:
                    line = next(ln for t, ln in m.instantiates if t in made)
                    smells.append(Smell("NEW_IN_LOGIC", c.file, line, line, f"{c.name}.{m.name}",
                                        f"`{m.name}` constructs {', '.join(made)} itself, so it can't be swapped "
                                        f"or faked"))

        non_ctor = [m for m in c.methods if not m.ctor]
        for f in c.fields:
            if base_type(f.type) in UNSAFE_MUTABLE_TYPES:
                continue
            branch = [m.name for m in non_ctor if f.name in m.branches_on]
            assign = [m.name for m in non_ctor if f.name in m.assigns_const]
            if len(branch) >= 2 and len(assign) >= 2:
                smells.append(Smell("STATE_FLAG", c.file, f.line, f.line, f"{c.name}.{f.name}",
                                    f"`{f.name}` is switched on in {', '.join(branch)} and reassigned in "
                                    f"{', '.join(assign)}"))

        if concurrency and not c.is_value:
            fields = {f.name: f for f in c.fields}
            hits: dict[str, int] = {}
            for m in c.methods:
                if m.ctor or m.private or m.synchronized:
                    continue
                for fname, line in m.unguarded:
                    f = fields.get(fname)
                    if f is None or any(h in (f.init_type or "") + (f.type or "") for h in THREAD_SAFE_HINTS):
                        continue
                    bt = base_type(f.type) or base_type(f.init_type)
                    if bt in UNSAFE_MUTABLE_TYPES or bt in COUNTER_TYPES or bt.endswith("[]"):
                        hits.setdefault(fname, line)
            if hits:
                first = min(hits.values())
                names = ", ".join(f"`{n}`" for n in sorted(hits, key=hits.get))
                smells.append(Smell("UNGUARDED_SHARED", c.file, first, first, c.name,
                                    f"{names} {'is' if len(hits) == 1 else 'are'} modified with no lock held; "
                                    f"concurrent callers can interleave"))
    return smells
