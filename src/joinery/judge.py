"""Runs a workspace's solution against problem suites inside a Docker sandbox."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from . import codegen
from .problems import REPO_ROOT, Problem, get_problem

RUNNERS_DIR = REPO_ROOT / "runners"
JOBS_DIR = Path(os.environ.get("JOINERY_JOBS", Path.home() / ".cache" / "joinery" / "jobs"))
WORKSPACE_META = ".joinery.json"

LIMITS = {
    "memory": "512m",
    "pids": "256",
    "tmpfs": "/tmp:rw,size=256m",
}
WALL_TIMEOUT_S = 180


class JudgeError(RuntimeError):
    pass


@dataclass
class Workspace:
    root: Path
    problem: Problem
    lang: str

    @classmethod
    def open(cls, root: Path) -> "Workspace":
        meta_path = root / WORKSPACE_META
        if not meta_path.exists():
            raise JudgeError(f"{root} is not a joinery workspace (no {WORKSPACE_META}); run `joinery scaffold` first")
        meta = json.loads(meta_path.read_text())
        return cls(root.resolve(), get_problem(meta["problem"]), meta["lang"])

    @property
    def solution_dir(self) -> Path:
        return self.root / "solution"


def scaffold(problem: Problem, lang: str, dest: Path) -> list[Path]:
    if lang not in codegen.LANGS:
        raise JudgeError(f"unsupported language {lang!r} (choose: {', '.join(codegen.LANGS)})")
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / WORKSPACE_META).exists():
        existing = json.loads((dest / WORKSPACE_META).read_text())
        if existing != {"problem": problem.id, "lang": lang}:
            raise JudgeError(f"{dest} is already a workspace for {existing}")
    written = codegen.write_files(dest, codegen.contract_files(problem.contract, lang))
    written += codegen.write_files(dest, codegen.stub_files(problem.contract, lang), overwrite=False)
    written += codegen.write_files(dest, {"PROBLEM.md": problem.statement, WORKSPACE_META: json.dumps(
        {"problem": problem.id, "lang": lang}, indent=2) + "\n"})
    return written


# ------------------------------------------------------------------ docker


def docker_bin() -> str:
    found = shutil.which("docker")
    if found:
        return found
    orb = Path.home() / ".orbstack" / "bin" / "docker"
    if orb.exists():
        return str(orb)
    raise JudgeError("docker not found. Install OrbStack (`brew install --cask orbstack`) and open it once.")


def image_tag(lang: str) -> str:
    """Tag derived from the runner sources, so editing a runner rebuilds its image."""
    h = hashlib.sha256()
    root = RUNNERS_DIR / lang
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return f"joinery-{lang}:{h.hexdigest()[:12]}"


def ensure_image(lang: str, force: bool = False, quiet: bool = True) -> str:
    tag = image_tag(lang)
    docker = docker_bin()
    if not force:
        probe = subprocess.run([docker, "image", "inspect", tag], capture_output=True)
        if probe.returncode == 0:
            return tag
    proc = subprocess.run(
        [docker, "build", "-q" if quiet else "--progress=plain", "-t", tag, str(RUNNERS_DIR / lang)],
        capture_output=quiet, text=True,
    )
    if proc.returncode != 0:
        raise JudgeError(f"building runner image {tag} failed:\n{(proc.stderr or '')[-3000:]}")
    return tag


def judge(ws: Workspace, suites: list[str]) -> dict:
    """Run the given suites; returns the runner's result dict (status + suites)."""
    if not ws.solution_dir.is_dir():
        raise JudgeError(f"{ws.solution_dir} does not exist")
    problem, lang = ws.problem, ws.lang
    image = ensure_image(lang)
    docker = docker_bin()

    job = JOBS_DIR / uuid.uuid4().hex[:12]
    job.mkdir(parents=True)
    try:
        # Fresh contract every run: the workspace copy is for the IDE only.
        codegen.write_files(job, codegen.contract_files(problem.contract, lang))
        (job / "contract.json").write_text(json.dumps(problem.contract.to_json()))
        (job / "scenarios.json").write_text(json.dumps({"suites": [problem.suite(s) for s in suites]}))
        for p in [job, *job.rglob("*")]:
            p.chmod(0o777 if p.is_dir() else 0o666)

        name = f"joinery-{job.name}"
        cmd = [
            docker, "run", "--rm", "--name", name,
            "--network", "none",
            "--read-only", "--tmpfs", LIMITS["tmpfs"],
            "--memory", LIMITS["memory"], "--memory-swap", LIMITS["memory"],
            "--cpus", "4" if "concurrency" in suites else "1",
            "--pids-limit", LIMITS["pids"],
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "-v", f"{job}:/job",
            "-v", f"{ws.solution_dir}:/work/solution:ro",
            image,
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=WALL_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            subprocess.run([docker, "kill", name], capture_output=True)
            return {"status": "killed", "message": f"run exceeded {WALL_TIMEOUT_S}s wall clock"}

        result_path = job / "result.json"
        if not result_path.exists():
            out = (proc.stdout + proc.stderr)[-3000:]
            if proc.returncode == 137:
                return {"status": "killed", "message": f"container killed (memory limit {LIMITS['memory']}?)\n{out}"}
            return {"status": "runner_crashed", "message": f"exit {proc.returncode}\n{out}"}
        return json.loads(result_path.read_text())
    finally:
        shutil.rmtree(job, ignore_errors=True)
