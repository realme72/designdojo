"""Loading problem packages from problems/<id>/."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import yaml

from .contract import Contract, load_contract

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBLEMS_DIR = Path(os.environ.get("JOINERY_PROBLEMS", REPO_ROOT / "problems"))

# Suites in run order. "visible" suites show full expected/actual on failure.
SUITES = ("sample", "hidden", "concurrency")
VISIBLE_SUITES = {"sample"}


class ProblemError(LookupError):
    pass


@dataclass
class Problem:
    id: str
    root: Path

    @cached_property
    def meta(self) -> dict:
        return yaml.safe_load((self.root / "problem.yaml").read_text())

    @property
    def title(self) -> str:
        return self.meta.get("title", self.id)

    @cached_property
    def contract(self) -> Contract:
        return load_contract(self.root / "contract.yaml")

    @property
    def concurrency(self) -> bool:
        return "concurrency" in (self.meta.get("tags") or [])

    @property
    def contract_types(self) -> set[str]:
        c = self.contract
        return set(c.interfaces) | set(c.provided)

    @property
    def statement(self) -> str:
        return (self.root / self.meta.get("statement", "statement.md")).read_text()

    def suite(self, name: str) -> dict:
        """Load a scenario suite, applying the file-level default config."""
        path = self.root / "scenarios" / f"{name}.yaml"
        if not path.exists():
            return {"name": name, "scenarios": []}
        raw = yaml.safe_load(path.read_text()) or {}
        defaults = {k: v for k, v in raw.items() if k != "scenarios"}
        scenarios = []
        seen = set()
        for sc in raw.get("scenarios") or []:
            if sc["name"] in seen:
                raise ProblemError(f"{path}: duplicate scenario {sc['name']!r}")
            seen.add(sc["name"])
            scenarios.append({**defaults, **sc})
        return {"name": name, "scenarios": scenarios}


def list_problems() -> list[Problem]:
    if not PROBLEMS_DIR.is_dir():
        return []
    return [Problem(p.name, p) for p in sorted(PROBLEMS_DIR.iterdir()) if (p / "problem.yaml").exists()]


def get_problem(problem_id: str) -> Problem:
    root = PROBLEMS_DIR / problem_id
    if not (root / "problem.yaml").exists():
        known = ", ".join(p.id for p in list_problems()) or "none"
        raise ProblemError(f"unknown problem {problem_id!r} (available: {known})")
    return Problem(problem_id, root)
