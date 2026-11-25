"""Python source -> model (tree-sitter). Also emits the Python-specific syntactic smells."""

from __future__ import annotations

import re

import tree_sitter as ts
import tree_sitter_python as tsp

from .model import PY_MUTATORS, ClassInfo, Field, Method, Smell

PARSER = ts.Parser(ts.Language(tsp.language()))
CONST = re.compile(r"^(?:[A-Za-z_]\w*\.)*[A-Z][A-Z0-9_]*$")
UPPER = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
TIME_CALLS = {"time.time", "time.time_ns", "datetime.now", "datetime.datetime.now", "datetime.utcnow",
              "datetime.datetime.utcnow", "date.today", "datetime.date.today"}
HEAP_MUTATORS = {"heapq.heappush", "heapq.heappop", "heapq.heapify", "heapq.heapreplace", "heapq.heappushpop",
                 "heappush", "heappop", "heapify", "bisect.insort", "insort", "bisect.insort_left", "bisect.insort_right"}
MUTABLE_CALLS = {"list", "dict", "set", "defaultdict", "deque", "Counter", "OrderedDict",
                 "collections.defaultdict", "collections.deque", "collections.Counter", "collections.OrderedDict"}
LOCK_TYPES = {"Lock", "RLock", "Condition", "Semaphore", "BoundedSemaphore"}
LITERALS = {"true", "false", "none", "integer", "float", "string"}


def _t(n: ts.Node | None) -> str:
    return n.text.decode() if n is not None else ""


def _line(n: ts.Node) -> int:
    return n.start_point[0] + 1


def _end(n: ts.Node) -> int:
    return n.end_point[0] + 1


def _walk(n: ts.Node):
    stack = [n]
    while stack:
        x = stack.pop()
        yield x
        stack.extend(reversed(x.named_children))


def _self_attr(n: ts.Node | None) -> str | None:
    if n is not None and n.type == "attribute" and _t(n.child_by_field_name("object")) == "self":
        return _t(n.child_by_field_name("attribute"))
    return None


def _base_field(n: ts.Node | None) -> str | None:
    """self.free[size].append(x) -> free."""
    while n is not None:
        f = _self_attr(n)
        if f:
            return f
        if n.type == "subscript":
            n = n.child_by_field_name("value")
        elif n.type == "attribute":
            n = n.child_by_field_name("object")
        elif n.type == "call":
            n = n.child_by_field_name("function")
        elif n.type == "parenthesized_expression":
            n = n.named_children[0] if n.named_children else None
        else:
            return None
    return None


def _value_type(v: ts.Node | None) -> str | None:
    """Best-effort type of an initializer expression."""
    if v is None:
        return None
    if v.type in ("dictionary", "dictionary_comprehension"):
        return "dict"
    if v.type in ("list", "list_comprehension"):
        return "list"
    if v.type in ("set", "set_comprehension"):
        return "set"
    if v.type == "integer":
        return "int"
    if v.type in ("true", "false"):
        return "bool"
    if v.type == "string":
        return "str"
    if v.type == "call":
        fn = _t(v.child_by_field_name("function"))
        return fn.split(".")[-1]
    return None


def _is_mutable_value(v: ts.Node | None) -> bool:
    if v is None:
        return False
    if v.type in ("dictionary", "list", "set", "dictionary_comprehension", "list_comprehension", "set_comprehension"):
        return True
    return v.type == "call" and _t(v.child_by_field_name("function")) in MUTABLE_CALLS


def _params(fn: ts.Node) -> list[tuple[str, str | None]]:
    out = []
    for p in (fn.child_by_field_name("parameters") or fn).named_children:
        if p.type == "identifier":
            out.append((_t(p), None))
        elif p.type == "typed_parameter":
            ident = next((c for c in p.named_children if c.type == "identifier"), None)
            out.append((_t(ident), _t(p.child_by_field_name("type"))))
        elif p.type in ("default_parameter", "typed_default_parameter"):
            out.append((_t(p.child_by_field_name("name")), _t(p.child_by_field_name("type")) or None))
    return [(n, t) for n, t in out if n not in ("self", "cls")]


class _BodyScan:
    def __init__(self, m: Method, method_names: set[str], lock_fields: set[str]):
        self.m = m
        self.method_names = method_names
        self.lock_fields = lock_fields
        self.time_calls: list[tuple[str, int]] = []

    def mutate(self, f: str, n: ts.Node, guarded: bool):
        self.m.mutates.add(f)
        if not guarded:
            self.m.unguarded.append((f, _line(n)))

    def cond(self, n: ts.Node | None):
        if n is None:
            return
        for x in _walk(n):
            f = _self_attr(x)
            if f:
                self.m.branches_on.add(f)

    def is_lock(self, with_stmt: ts.Node) -> bool:
        for item in _walk(with_stmt):
            if item.type == "with_item":
                v = item.child_by_field_name("value")
                if "lock" in _t(v).lower() or _self_attr(v) in self.lock_fields:
                    return True
        return False

    def visit(self, n: ts.Node, guarded: bool):
        t = n.type
        if t in ("class_definition", "function_definition", "lambda"):
            return  # nested scopes are not this method's direct behaviour
        if t == "with_statement" and self.is_lock(n):
            for c in n.named_children:
                self.visit(c, True)
            return
        if t == "assignment":
            left, right = n.child_by_field_name("left"), n.child_by_field_name("right")
            f = _self_attr(left)
            if f:
                self.m.writes.add(f)
                if right is not None and (right.type in LITERALS or CONST.match(_t(right))):
                    self.m.assigns_const.add(f)
            elif left is not None and left.type == "subscript":
                bf = _base_field(left)
                if bf:
                    self.mutate(bf, n, guarded)
            if right is not None:
                self.visit(right, guarded)
            if left is not None and left.type == "subscript":
                self.visit(left.child_by_field_name("subscript") or left, guarded)
            return
        if t == "augmented_assignment":
            bf = _base_field(n.child_by_field_name("left"))
            if bf:
                self.mutate(bf, n, guarded)
            right = n.child_by_field_name("right")
            if right is not None:
                self.visit(right, guarded)
            return
        if t == "delete_statement":
            for c in n.named_children:
                bf = _base_field(c) if c.type == "subscript" else None
                if bf:
                    self.mutate(bf, n, guarded)
        elif t == "call":
            fn = n.child_by_field_name("function")
            fname = _t(fn)
            if fn is not None and fn.type == "attribute":
                obj, attr = fn.child_by_field_name("object"), _t(fn.child_by_field_name("attribute"))
                if _t(obj) == "self" and attr in self.method_names:
                    self.m.calls_self.add(attr)
                else:
                    bf = _base_field(obj)
                    if bf and attr in PY_MUTATORS:
                        self.mutate(bf, n, guarded)
            if fname in HEAP_MUTATORS:
                args = n.child_by_field_name("arguments")
                first = args.named_children[0] if args is not None and args.named_children else None
                bf = _base_field(first)
                if bf:
                    self.mutate(bf, n, guarded)
            if fname in TIME_CALLS:
                self.time_calls.append((fname + "()", _line(n)))
            last = fname.split(".")[-1]
            if last[:1].isupper() and not UPPER.match(last):
                self.m.instantiates.append((last, _line(n)))
        elif t in ("if_statement", "elif_clause", "while_statement"):
            self.cond(n.child_by_field_name("condition"))
        elif t == "conditional_expression" and len(n.named_children) == 3:
            self.cond(n.named_children[1])
        elif t == "match_statement":
            self.cond(n.child_by_field_name("subject"))
        else:
            f = _self_attr(n)
            if f:
                self.m.reads.add(f)
                return
        for c in n.named_children:
            self.visit(c, guarded)


def _decorators(n: ts.Node) -> list[str]:
    if n.parent is not None and n.parent.type == "decorated_definition":
        return [_t(d).lstrip("@").split("(")[0] for d in n.parent.named_children if d.type == "decorator"]
    return []


def parse_file(src: bytes, rel: str) -> tuple[list[ClassInfo], list[Smell]]:
    tree = PARSER.parse(src)
    classes: list[ClassInfo] = []
    smells: list[Smell] = []
    root = tree.root_node
    for node in _walk(root):
        if node.type == "class_definition":
            c, s = _class(node, rel)
            classes.append(c)
            smells += s
        elif node.type == "if_statement":
            smells += _if_chain_smell(node, rel)
        elif node.type == "match_statement":
            cases = [c for c in _walk(node) if c.type == "case_clause"]
            if len(cases) >= 3:
                subj = _t(node.child_by_field_name("subject"))
                smells.append(Smell("TYPE_SWITCH", rel, _line(node), _end(node), subj,
                                    f"match on `{subj}` with {len(cases)} cases"))
        elif node.type == "global_statement":
            smells.append(Smell("GLOBAL_STATE", rel, _line(node), _line(node), _t(node),
                                f"`{_t(node)}` mutates module-level state"))
    # module-level mutable state
    for stmt in root.named_children:
        if stmt.type == "expression_statement" and stmt.named_children and stmt.named_children[0].type == "assignment":
            a = stmt.named_children[0]
            name = _t(a.child_by_field_name("left"))
            if not UPPER.match(name) and _is_mutable_value(a.child_by_field_name("right")):
                smells.append(Smell("GLOBAL_STATE", rel, _line(a), _line(a), name,
                                    f"module-level mutable `{name}` is shared by every instance and thread"))
    return classes, smells


def _class(node: ts.Node, rel: str) -> tuple[ClassInfo, list[Smell]]:
    name = _t(node.child_by_field_name("name"))
    bases = [_t(b) for b in (node.child_by_field_name("superclasses") or node).named_children
             if b.type in ("identifier", "attribute")] if node.child_by_field_name("superclasses") else []
    bases = [b.split(".")[-1] for b in bases]
    decos = _decorators(node)
    body = node.child_by_field_name("body")
    smells: list[Smell] = []

    funcs: list[tuple[ts.Node, list[str]]] = []
    class_assigns: list[ts.Node] = []
    for c in (body.named_children if body is not None else []):
        if c.type == "function_definition":
            funcs.append((c, []))
        elif c.type == "decorated_definition":
            d = c.child_by_field_name("definition")
            if d is not None and d.type == "function_definition":
                funcs.append((d, _decorators(d)))
        elif c.type == "expression_statement" and c.named_children and c.named_children[0].type == "assignment":
            class_assigns.append(c.named_children[0])

    has_abstract = any("abstractmethod" in " ".join(ds) for _, ds in funcs)
    if any(b in ("Enum", "IntEnum", "StrEnum", "Flag", "IntFlag") for b in bases):
        kind = "enum"
    elif any(d.split(".")[-1] == "dataclass" for d in decos):
        kind = "dataclass"
    elif any(b.endswith(("Exception", "Error")) for b in bases):
        kind = "exception"
    elif "Protocol" in bases or (has_abstract and all("abstractmethod" in " ".join(ds) or f.child_by_field_name("name")
                                                       and _t(f.child_by_field_name("name")) == "__init__"
                                                       for f, ds in funcs)):
        kind = "interface"
    elif has_abstract or "ABC" in bases:
        kind = "abstract"
    else:
        kind = "class"

    extends = [b for b in bases if b not in ("ABC", "Protocol", "object", "Generic", "Enum", "IntEnum", "StrEnum")]
    ci = ClassInfo(name, kind, rel, _line(node), _end(node), extends, [])

    # class-level fields
    for a in class_assigns:
        fname = _t(a.child_by_field_name("left"))
        right = a.child_by_field_name("right")
        ftype = _t(a.child_by_field_name("type")) or _value_type(right)
        instance_level = kind == "dataclass"
        ci.fields.append(Field(fname, ftype, _line(a), static=not instance_level))
        if kind in ("class", "abstract") and not UPPER.match(fname) and _is_mutable_value(right):
            smells.append(Smell("GLOBAL_STATE", rel, _line(a), _line(a), f"{name}.{fname}",
                                f"class attribute `{fname}` is one object shared by every {name} instance"))

    # instance fields: self.x = ... anywhere (types from annotations / ctor params / initializers)
    seen: dict[str, Field] = {}
    for fn, _ in funcs:
        params = dict(_params(fn))
        for x in _walk(fn):
            if x.type != "assignment":
                continue
            f = _self_attr(x.child_by_field_name("left"))
            if not f:
                continue
            right = x.child_by_field_name("right")
            ftype = _t(x.child_by_field_name("type")) or None
            if not ftype and right is not None and right.type == "identifier":
                ftype = params.get(_t(right))
            ftype = ftype or _value_type(right)
            if f not in seen:
                seen[f] = Field(f, ftype, _line(x), init_type=_t(right) or None)
                ci.fields.append(seen[f])
            elif seen[f].type is None and ftype:
                seen[f].type = ftype
        # tuple assignment: self.a, self.b = a, b
        for x in _walk(fn):
            if x.type == "assignment" and (x.child_by_field_name("left") or x).type == "pattern_list":
                for el in x.child_by_field_name("left").named_children:
                    f = _self_attr(el)
                    if f and f not in seen:
                        seen[f] = Field(f, None, _line(x))
                        ci.fields.append(seen[f])

    lock_fields = {f.name for f in ci.fields if (f.type or "").split(".")[-1] in LOCK_TYPES}
    method_names = {_t(f.child_by_field_name("name")) for f, _ in funcs}
    for fn, ds in funcs:
        mname = _t(fn.child_by_field_name("name"))
        params = _params(fn)
        m = Method(
            name=mname, line_start=_line(fn), line_end=_end(fn), params=[p for p, _ in params],
            static=any(d in ("staticmethod", "classmethod") for d in ds),
            abstract=any(d.split(".")[-1] == "abstractmethod" for d in ds),
            ctor=mname == "__init__",
            private=mname.startswith("_") and not mname.startswith("__"),
        )
        scan = _BodyScan(m, method_names, lock_fields)
        fbody = fn.child_by_field_name("body")
        if fbody is not None:
            for c in fbody.named_children:
                scan.visit(c, False)
            for what, ln in scan.time_calls:
                smells.append(Smell("DIRECT_TIME", rel, ln, ln, f"{name}.{mname}",
                                    f"`{what}` reads the system clock instead of an injected Clock"))
            stmts = [s for s in fbody.named_children
                     if not (s.type == "expression_statement" and s.named_children
                             and s.named_children[0].type == "string")]
            if (not m.abstract and not m.ctor and ci.extends and kind not in ("interface", "abstract")
                    and len(stmts) == 1 and stmts[0].type == "raise_statement"
                    and "NotImplementedError" in _t(stmts[0])):
                smells.append(Smell("REFUSED_BEQUEST", rel, m.line_start, m.line_end, f"{name}.{mname}",
                                    f"`{mname}` is inherited but only raises NotImplementedError"))
        ci.methods.append(m)

    if ci.method("__new__") or any(f.name == "_instance" and f.static for f in ci.fields):
        smells.append(Smell("SPECULATIVE_PATTERN", rel, ci.line_start, ci.line_start, name,
                            f"`{name}` is a Singleton: global access point, hard to substitute in tests", "info"))
    return ci, smells


def _subject(cond: ts.Node) -> str | None:
    for x in _walk(cond):
        if x.type == "call" and _t(x.child_by_field_name("function")) == "isinstance":
            args = x.child_by_field_name("arguments")
            if args is not None and args.named_children:
                return _t(args.named_children[0])
        if x.type == "comparison_operator" and len(x.named_children) == 2:
            l, r = x.named_children
            ops = [_t(c) for c in x.children if not c.is_named]
            if any(o in ("==", "is", "!=", "is not") for o in ops):
                if CONST.match(_t(r)):
                    return _t(l)
                if CONST.match(_t(l)):
                    return _t(r)
    return None


def _if_chain_smell(n: ts.Node, rel: str) -> list[Smell]:
    conds = [n.child_by_field_name("condition")]
    has_else = False
    for alt in n.children_by_field_name("alternative"):
        if alt.type == "elif_clause":
            conds.append(alt.child_by_field_name("condition"))
        elif alt.type == "else_clause":
            has_else = True
    branches = len(conds) + (1 if has_else else 0)
    if branches < 3:
        return []
    subjects = [s for s in (_subject(c) for c in conds if c is not None) if s]
    for s in set(subjects):
        if subjects.count(s) >= 2:
            return [Smell("TYPE_SWITCH", rel, _line(n), _end(n), s,
                          f"if/elif chain with {branches} branches on `{s}`")]
    return []
