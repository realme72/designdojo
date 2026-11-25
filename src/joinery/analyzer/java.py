"""Java source -> model (tree-sitter). Also emits the Java-specific syntactic smells."""

from __future__ import annotations

import re

import tree_sitter as ts
import tree_sitter_java as tsj

from .model import JAVA_MUTATORS, UNSAFE_MUTABLE_TYPES, ClassInfo, Field, Method, Smell

PARSER = ts.Parser(ts.Language(tsj.language()))
CLASS_NODES = {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration"}
CONST = re.compile(r"^(?:[A-Za-z_]\w*\.)*[A-Z][A-Z0-9_]*$")
TIME_CALLS = re.compile(r"^(System\.currentTimeMillis|Instant\.now|LocalDateTime\.now|LocalDate\.now|ZonedDateTime\.now|"
                        r"OffsetDateTime\.now|Clock\.system\w*|LocalTime\.now)\b")


def _t(n: ts.Node | None) -> str:
    return n.text.decode() if n is not None else ""


def _line(n: ts.Node) -> int:
    return n.start_point[0] + 1


def _end(n: ts.Node) -> int:
    return n.end_point[0] + 1


def _mods(n: ts.Node) -> set[str]:
    for c in n.children:
        if c.type == "modifiers":
            return {_t(x) for x in c.children}
    return set()


def type_name(n: ts.Node | None) -> str:
    """Base type name without generics/package: Map<String, X> -> Map, java.util.List -> List."""
    if n is None:
        return ""
    if n.type == "generic_type":
        return type_name(n.named_children[0])
    if n.type == "scoped_type_identifier":
        return _t(n).split(".")[-1]
    if n.type == "array_type":
        return type_name(n.child_by_field_name("element")) + "[]"
    return _t(n)


def _type_list(n: ts.Node | None) -> list[str]:
    if n is None:
        return []
    out = []
    for c in n.named_children:
        if c.type == "type_list":
            out += [type_name(x) for x in c.named_children]
        else:
            out.append(type_name(c))
    return out


def _skip_nested(n: ts.Node) -> bool:
    return n.type in CLASS_NODES or (n.type == "class_body" and n.parent is not None
                                     and n.parent.type == "object_creation_expression")


class _BodyScan:
    """Walks one method body, recording how it touches its own class's fields."""

    def __init__(self, m: Method, fields: set[str], params: list[str], method_names: set[str]):
        self.m = m
        self.fields = fields
        self.locals = set(params)
        self.method_names = method_names
        self.unguarded: list[tuple[str, int]] = []
        self.time_calls: list[tuple[str, int]] = []

    def field_ref(self, n: ts.Node | None) -> str | None:
        if n is None:
            return None
        if n.type == "field_access" and _t(n.child_by_field_name("object")) == "this":
            return _t(n.child_by_field_name("field"))
        if n.type == "identifier" and _t(n) in self.fields and _t(n) not in self.locals:
            return _t(n)
        return None

    def base_field(self, n: ts.Node | None) -> str | None:
        """Field at the root of an access chain: this.free.get(k).poll() -> free."""
        while n is not None:
            f = self.field_ref(n)
            if f:
                return f
            if n.type == "method_invocation":
                n = n.child_by_field_name("object")
            elif n.type == "array_access":
                n = n.child_by_field_name("array")
            elif n.type == "field_access":
                n = n.child_by_field_name("object")
            elif n.type == "parenthesized_expression":
                n = n.named_children[0] if n.named_children else None
            else:
                return None
        return None

    def mutate(self, f: str, n: ts.Node, guarded: bool):
        self.m.mutates.add(f)
        if not guarded:
            self.unguarded.append((f, _line(n)))

    def cond(self, n: ts.Node | None):
        if n is None:
            return
        for x in _walk(n):
            f = self.field_ref(x)
            if f:
                self.m.branches_on.add(f)

    def visit(self, n: ts.Node, guarded: bool):
        if _skip_nested(n):
            return
        t = n.type
        if t == "local_variable_declaration":
            for d in n.named_children:
                if d.type == "variable_declarator":
                    self.locals.add(_t(d.child_by_field_name("name")))
        elif t in ("formal_parameter", "catch_formal_parameter", "enhanced_for_statement"):
            name = n.child_by_field_name("name")
            if name is not None:
                self.locals.add(_t(name))
        elif t == "lambda_expression":
            for p in _walk(n.child_by_field_name("parameters") or n):
                if p.type == "identifier":
                    self.locals.add(_t(p))
                    break
        elif t == "synchronized_statement":
            for c in n.named_children:
                self.visit(c, True)
            return
        elif t == "assignment_expression":
            left = n.child_by_field_name("left")
            right = n.child_by_field_name("right")
            op = _t(n.child_by_field_name("operator"))
            f = self.field_ref(left)
            if f:
                if op == "=":
                    self.m.writes.add(f)
                    if right is not None and (right.type in ("true", "false", "decimal_integer_literal", "string_literal",
                                                             "null_literal", "character_literal")
                                              or CONST.match(_t(right))):
                        self.m.assigns_const.add(f)
                else:
                    self.mutate(f, n, guarded)
            elif left is not None and left.type == "array_access":
                bf = self.base_field(left)
                if bf:
                    self.mutate(bf, n, guarded)
            # still visit the right side for reads/calls
            if right is not None:
                self.visit(right, guarded)
            return
        elif t == "update_expression":
            target = next((c for c in n.named_children), None)
            bf = self.field_ref(target) or self.base_field(target)
            if bf:
                self.mutate(bf, n, guarded)
        elif t == "method_invocation":
            obj = n.child_by_field_name("object")
            name = _t(n.child_by_field_name("name"))
            if obj is None or _t(obj) == "this":
                if name in self.method_names:
                    self.m.calls_self.add(name)
            else:
                bf = self.base_field(obj)
                if bf and name in JAVA_MUTATORS:
                    self.mutate(bf, n, guarded)
            full = (_t(obj) + "." if obj is not None else "") + name
            if TIME_CALLS.match(full):
                self.time_calls.append((full + "()", _line(n)))
        elif t == "object_creation_expression":
            tn = type_name(n.child_by_field_name("type"))
            self.m.instantiates.append((tn, _line(n)))
            if tn == "Date" and not n.child_by_field_name("arguments").named_children:
                self.time_calls.append(("new Date()", _line(n)))
        elif t in ("if_statement", "while_statement", "do_statement", "ternary_expression"):
            self.cond(n.child_by_field_name("condition"))
        elif t in ("switch_expression", "switch_statement"):
            self.cond(n.child_by_field_name("condition"))
        else:
            f = self.field_ref(n)
            if f:
                self.m.reads.add(f)
        for c in n.named_children:
            self.visit(c, guarded)


def _walk(n: ts.Node):
    stack = [n]
    while stack:
        x = stack.pop()
        yield x
        stack.extend(reversed(x.named_children))


def _class_kind(n: ts.Node, mods: set[str], extends: list[str]) -> str:
    if n.type == "interface_declaration":
        return "interface"
    if n.type == "enum_declaration":
        return "enum"
    if n.type == "record_declaration":
        return "record"
    if any(e.endswith(("Exception", "Error", "Throwable")) for e in extends):
        return "exception"
    return "abstract" if "abstract" in mods else "class"


def _members(body: ts.Node | None) -> list[ts.Node]:
    if body is None:
        return []
    out = []
    for c in body.named_children:
        if c.type == "enum_body_declarations":
            out += c.named_children
        else:
            out.append(c)
    return out


def parse_file(src: bytes, rel: str) -> tuple[list[ClassInfo], list[Smell]]:
    tree = PARSER.parse(src)
    classes: list[ClassInfo] = []
    smells: list[Smell] = []
    for node in _walk(tree.root_node):
        if node.type in CLASS_NODES:
            c, s = _class(node, rel)
            classes.append(c)
            smells += s
    for node in _walk(tree.root_node):
        if node.type in ("switch_expression", "switch_statement"):
            smells += _switch_smell(node, rel)
        elif node.type == "if_statement" and not (node.parent is not None and node.parent.type == "if_statement"
                                                   and node.parent.child_by_field_name("alternative") == node):
            smells += _if_chain_smell(node, rel)
    return classes, smells


def _class(node: ts.Node, rel: str) -> tuple[ClassInfo, list[Smell]]:
    mods = _mods(node)
    name = _t(node.child_by_field_name("name"))
    if node.type == "interface_declaration":
        extends = _type_list(next((c for c in node.named_children if c.type == "extends_interfaces"), None))
        implements: list[str] = []
    else:
        sup = node.child_by_field_name("superclass")
        extends = [type_name(sup.named_children[0])] if sup is not None and sup.named_children else []
        implements = _type_list(node.child_by_field_name("interfaces"))
    kind = _class_kind(node, mods, extends)
    ci = ClassInfo(name, kind, rel, _line(node), _end(node), extends, implements)
    smells: list[Smell] = []
    body = node.child_by_field_name("body")
    members = _members(body)
    init_types: dict[str, str] = {}

    if node.type == "record_declaration":
        for p in (node.child_by_field_name("parameters") or node).named_children:
            if p.type == "formal_parameter":
                ci.fields.append(Field(_t(p.child_by_field_name("name")), _t(p.child_by_field_name("type")), _line(p),
                                       final=True))

    for mnode in members:
        if mnode.type in ("field_declaration", "constant_declaration"):
            fm = _mods(mnode)
            ftype = mnode.child_by_field_name("type")
            for d in mnode.named_children:
                if d.type != "variable_declarator":
                    continue
                fname = _t(d.child_by_field_name("name"))
                static = "static" in fm or node.type == "interface_declaration"
                final = "final" in fm or node.type == "interface_declaration"
                ci.fields.append(Field(fname, _t(ftype), _line(d), static, final))
                value = d.child_by_field_name("value")
                if value is not None:
                    init_types[fname] = _t(value)
                if static and not final and node.type != "interface_declaration":
                    smells.append(Smell("GLOBAL_STATE", rel, _line(d), _line(d), f"{name}.{fname}",
                                        f"static non-final field `{fname}` is shared, mutable state"))
                elif static and value is not None and value.type == "object_creation_expression" \
                        and type_name(value.child_by_field_name("type")) in UNSAFE_MUTABLE_TYPES:
                    smells.append(Smell("GLOBAL_STATE", rel, _line(d), _line(d), f"{name}.{fname}",
                                        f"static collection `{fname}` is global mutable state"))

    fields = {f.name for f in ci.fields}
    method_names = {_t(m.child_by_field_name("name")) for m in members
                    if m.type in ("method_declaration", "constructor_declaration")}
    for mnode in members:
        if mnode.type not in ("method_declaration", "constructor_declaration", "compact_constructor_declaration"):
            continue
        mm = _mods(mnode)
        ctor = mnode.type != "method_declaration"
        params = [_t(p.child_by_field_name("name")) for p in (mnode.child_by_field_name("parameters") or mnode).named_children
                  if p.type in ("formal_parameter", "spread_parameter") and p.child_by_field_name("name") is not None]
        body_node = mnode.child_by_field_name("body")
        abstract = "abstract" in mm or (node.type == "interface_declaration" and body_node is None
                                        and "default" not in mm and "static" not in mm)
        m = Method(
            name=name if ctor else _t(mnode.child_by_field_name("name")),
            line_start=_line(mnode), line_end=_end(mnode), params=params,
            static="static" in mm, abstract=abstract, ctor=ctor, private="private" in mm,
            synchronized="synchronized" in mm,
        )
        if body_node is not None:
            scan = _BodyScan(m, fields, params, method_names)
            guarded = m.synchronized or ".lock()" in _t(body_node)
            for c in body_node.named_children:
                scan.visit(c, guarded)
            m.unguarded = scan.unguarded
            for what, ln in scan.time_calls:
                smells.append(Smell("DIRECT_TIME", rel, ln, ln, f"{name}.{m.name}",
                                    f"`{what}` reads the system clock instead of an injected Clock"))
            stmts = [s for s in body_node.named_children if s.type not in ("line_comment", "block_comment")]
            if (not ctor and not m.static and (ci.extends or ci.implements) and len(stmts) == 1
                    and stmts[0].type == "throw_statement" and "UnsupportedOperationException" in _t(stmts[0])):
                smells.append(Smell("REFUSED_BEQUEST", rel, m.line_start, m.line_end, f"{name}.{m.name}",
                                    f"`{m.name}` is inherited but only throws UnsupportedOperationException"))
        ci.methods.append(m)

    for f in ci.fields:
        f.init_type = init_types.get(f.name)

    # Singleton: static field of its own type + private constructor or getInstance()
    own_static = any(f.static and type_name_from_text(f.type) == name for f in ci.fields)
    private_ctor = any(m.ctor and m.private for m in ci.methods)
    if own_static and (private_ctor or ci.method("getInstance")):
        smells.append(Smell("SPECULATIVE_PATTERN", rel, ci.line_start, ci.line_start, name,
                            f"`{name}` is a Singleton: global access point, hard to substitute in tests", "info"))
    return ci, smells


def type_name_from_text(t: str | None) -> str:
    if not t:
        return ""
    return re.split(r"[<\[]", t.strip())[0].split(".")[-1]


def _switch_smell(n: ts.Node, rel: str) -> list[Smell]:
    body = n.child_by_field_name("body")
    if body is None:
        return []
    cases, has_default = 0, False
    for x in _walk(body):
        if x.type == "switch_label":
            if _t(x).strip().startswith("default"):
                has_default = True
            else:
                cases += max(1, len(x.named_children))
    branches = cases + (1 if has_default else 0)
    if cases < 2 or branches < 3:  # same rule as if/else chains
        return []
    cond = n.child_by_field_name("condition")
    inner = cond.named_children[0] if cond is not None and cond.type == "parenthesized_expression" else cond
    subject = _t(inner)
    return [Smell("TYPE_SWITCH", rel, _line(n), _end(n), subject,
                  f"switch on `{subject}` with {branches} branches")]


def _subject(cond: ts.Node) -> str | None:
    for x in _walk(cond):
        if x.type == "instanceof_expression":
            return _t(x.child_by_field_name("left"))
        if x.type == "binary_expression" and _t(x.child_by_field_name("operator")) in ("==", "!="):
            l, r = x.child_by_field_name("left"), x.child_by_field_name("right")
            if CONST.match(_t(r)):
                return _t(l)
            if CONST.match(_t(l)):
                return _t(r)
    return None


def _if_chain_smell(n: ts.Node, rel: str) -> list[Smell]:
    conds, has_else, cur = [], False, n
    while cur is not None and cur.type == "if_statement":
        conds.append(cur.child_by_field_name("condition"))
        alt = cur.child_by_field_name("alternative")
        if alt is not None and alt.type != "if_statement":
            has_else = True
        cur = alt
    branches = len(conds) + (1 if has_else else 0)
    if branches < 3:
        return []
    subjects = [s for s in (_subject(c) for c in conds if c is not None) if s]
    for s in set(subjects):
        if subjects.count(s) >= 2:
            return [Smell("TYPE_SWITCH", rel, _line(n), _end(n), s,
                          f"if/else-if chain with {branches} branches on `{s}`")]
    return []
