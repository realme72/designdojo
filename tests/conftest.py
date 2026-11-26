import shutil
import subprocess
from pathlib import Path

import pytest

from designdojo.judge import JudgeError, docker_bin

ROOT = Path(__file__).resolve().parents[1]


def _docker_up() -> bool:
    try:
        return subprocess.run([docker_bin(), "info"], capture_output=True, timeout=20).returncode == 0
    except (JudgeError, subprocess.TimeoutExpired):
        return False


DOCKER = _docker_up()


def pytest_collection_modifyitems(config, items):
    if DOCKER:
        return
    skip = pytest.mark.skip(reason="Docker engine not running")
    for item in items:
        if "docker" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def workspace(tmp_path):
    """Make a scratch workspace from {path: source} for a language."""
    from designdojo.judge import Workspace, scaffold
    from designdojo.problems import get_problem

    def make(lang: str, files: dict[str, str], problem: str = "parking-lot") -> Workspace:
        dest = tmp_path / f"{problem}-{lang}"
        scaffold(get_problem(problem), lang, dest)
        for rel, src in files.items():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            (dest / rel).write_text(src)
        return Workspace.open(dest)

    return make
