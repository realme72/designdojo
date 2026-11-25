from __future__ import annotations

from pathlib import Path

from ..contract import Contract
from . import java, python

GENERATORS = {"java": java, "python": python}
LANGS = tuple(GENERATORS)


def write_files(root: Path, files: dict[str, str], overwrite: bool = True) -> list[Path]:
    written = []
    for rel, src in files.items():
        path = root / rel
        if path.exists() and not overwrite:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(src)
        written.append(path)
    return written


def contract_files(c: Contract, lang: str) -> dict[str, str]:
    return GENERATORS[lang].generate_contract(c)


def stub_files(c: Contract, lang: str) -> dict[str, str]:
    return GENERATORS[lang].generate_stub(c)
