"""Language-neutral problem contract: parsing, validation and normalization.

A contract (problems/<id>/contract.yaml) is the only surface the judge touches.
It is normalized here into plain dicts with parsed type trees, which are both
fed to the code generators and shipped as JSON to the in-container runners.

Type trees:  {"kind": "str"|"int"|"long"|"bool"|"void"}
             {"kind": "list", "of": T}
             {"kind": "map", "key": T, "value": T}
             {"kind": "enum"|"dto"|"iface", "name": "<Name>"}
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PRIMITIVES = ("str", "int", "long", "bool", "void")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ContractError(ValueError):
    pass


@dataclass
class Param:
    name: str
    type: dict


@dataclass
class Method:
    name: str
    params: list[Param]
    returns: dict
    raises: list[str] = field(default_factory=list)
    doc: str = ""


@dataclass
class Contract:
    package: str
    enums: dict[str, list[str]]
    dtos: dict[str, list[Param]]
    provided: dict[str, dict[str, Method]]
    interfaces: dict[str, dict[str, Method]]
    entrypoint: Method
    errors: list[str]
    docs: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> dict:
        def m(meth: Method) -> dict:
            return {
                "name": meth.name,
                "params": [{"name": p.name, "type": p.type} for p in meth.params],
                "returns": meth.returns,
                "raises": meth.raises,
            }

        return {
            "package": self.package,
            "enums": self.enums,
            "dtos": {k: [{"name": p.name, "type": p.type} for p in v] for k, v in self.dtos.items()},
            "provided": {k: {n: m(x) for n, x in v.items()} for k, v in self.provided.items()},
            "interfaces": {k: {n: m(x) for n, x in v.items()} for k, v in self.interfaces.items()},
            "entrypoint": m(self.entrypoint),
            "errors": self.errors,
        }


def parse_type(text: str, kinds: dict[str, str]) -> dict:
    tokens = re.findall(r"[A-Za-z_]\w*|[\[\],]", str(text))
    pos = 0

    def take(expected: str | None = None) -> str:
        nonlocal pos
        if pos >= len(tokens):
            raise ContractError(f"unexpected end of type {text!r}")
        tok = tokens[pos]
        if expected is not None and tok != expected:
            raise ContractError(f"expected {expected!r} in type {text!r}, got {tok!r}")
        pos += 1
        return tok

    def parse() -> dict:
        name = take()
        if name in ("list", "map"):
            take("[")
            args = [parse()]
            while pos < len(tokens) and tokens[pos] == ",":
                take(",")
                args.append(parse())
            take("]")
            if name == "list":
                if len(args) != 1:
                    raise ContractError(f"list takes one type argument: {text!r}")
                return {"kind": "list", "of": args[0]}
            if len(args) != 2:
                raise ContractError(f"map takes two type arguments: {text!r}")
            if args[0]["kind"] not in ("str", "int", "long", "enum"):
                raise ContractError(f"map keys must be str/int/long/enum: {text!r}")
            return {"kind": "map", "key": args[0], "value": args[1]}
        if name in PRIMITIVES:
            return {"kind": name}
        if name not in kinds:
            raise ContractError(f"unknown type {name!r} in {text!r}")
        return {"kind": kinds[name], "name": name}

    result = parse()
    if pos != len(tokens):
        raise ContractError(f"trailing tokens in type {text!r}")
    return result


def _ident(name: Any, what: str) -> str:
    if not isinstance(name, str) or not _IDENT.match(name):
        raise ContractError(f"invalid {what} name: {name!r}")
    return name


def _method(name: str, raw: dict | None, kinds: dict[str, str], errors: list[str]) -> Method:
    raw = raw or {}
    params = [
        Param(_ident(p, "parameter"), parse_type(t, kinds))
        for p, t in (raw.get("params") or {}).items()
    ]
    raises = list(raw.get("raises") or [])
    for e in raises:
        if e not in errors:
            raise ContractError(f"{name} raises undeclared error {e!r}")
    return Method(
        name=_ident(name, "method"),
        params=params,
        returns=parse_type(raw.get("returns", "void"), kinds),
        raises=raises,
        doc=str(raw.get("doc", "")).strip(),
    )


def load_contract(path: Path) -> Contract:
    return contract_from_raw(yaml.safe_load(path.read_text()))


def merge_patch(base: dict, patch: dict) -> dict:
    """Curveball contract patches: maps merge recursively, lists append new items (enum values,
    errors). Existing entries are never removed, so older scenarios keep working."""
    out = dict(base)
    for k, v in (patch or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = merge_patch(out[k], v)
        elif k in out and isinstance(out[k], list) and isinstance(v, list):
            out[k] = out[k] + [x for x in v if x not in out[k]]
        else:
            out[k] = v
    return out


def contract_from_raw(raw: dict) -> Contract:
    enums = {_ident(k, "enum"): [_ident(v, "enum value") for v in vals] for k, vals in (raw.get("enums") or {}).items()}
    dto_raw = raw.get("dtos") or {}
    provided_raw = raw.get("provided") or {}
    iface_raw = raw.get("interfaces") or {}
    errors = [_ident(e, "error") for e in (raw.get("errors") or [])]

    kinds: dict[str, str] = {}
    for group, kind in ((enums, "enum"), (dto_raw, "dto"), (provided_raw, "iface"), (iface_raw, "iface")):
        for name in group:
            if name in kinds:
                raise ContractError(f"duplicate type name {name!r}")
            kinds[_ident(name, kind)] = kind

    dtos = {
        name: [Param(_ident(f, "field"), parse_type(t, kinds)) for f, t in fields.items()]
        for name, fields in dto_raw.items()
    }
    provided = {
        name: {m: _method(m, spec, kinds, errors) for m, spec in (methods or {}).items()}
        for name, methods in provided_raw.items()
    }
    interfaces = {
        name: {m: _method(m, spec, kinds, errors) for m, spec in (methods or {}).items()}
        for name, methods in iface_raw.items()
    }
    ep_raw = raw.get("entrypoint") or {}
    entrypoint = _method(ep_raw.get("name", "create"), ep_raw, kinds, errors)
    if entrypoint.returns.get("kind") != "iface" or entrypoint.returns["name"] not in interfaces:
        raise ContractError("entrypoint must return one of the contract interfaces")

    return Contract(
        package=raw.get("package", "contract"),
        enums=enums,
        dtos=dtos,
        provided=provided,
        interfaces=interfaces,
        entrypoint=entrypoint,
        errors=errors,
        docs={k: str(v).strip() for k, v in (raw.get("docs") or {}).items()},
    )


def snake_to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(p[:1].upper() + p[1:] for p in rest)
