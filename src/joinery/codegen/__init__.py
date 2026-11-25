from __future__ import annotations

import os
import threading
from pathlib import Path

from ..contract import Contract
from . import java, python

GENERATORS = {"java": java, "python": python}
LANGS = tuple(GENERATORS)


def write_files(root: Path, files: dict[str, str], overwrite: bool = True) -> list[Path]:
    """Write atomically (temp + rename) and skip unchanged files, so concurrent readers never
    see a half-written file and editors don't see spurious changes."""
    written = []
    for rel, src in files.items():
        path = root / rel
        if path.exists() and (not overwrite or path.read_text() == src):
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(src)
        os.replace(tmp, path)
        written.append(path)
    return written


def contract_files(c: Contract, lang: str) -> dict[str, str]:
    return GENERATORS[lang].generate_contract(c)


def stub_files(c: Contract, lang: str) -> dict[str, str]:
    return GENERATORS[lang].generate_stub(c)
