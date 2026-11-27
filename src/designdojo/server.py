"""Local web server: JSON API over the judge, plus the built web UI.

Single user, localhost only. Workspaces live on disk under work/<problem>-<lang>/,
the same folders the CLI uses, so you can switch between the browser and your IDE.
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from pathlib import Path, PurePosixPath

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import codegen
from .judge import JudgeError, Workspace, judge, scaffold
from .problems import REPO_ROOT, ProblemError, get_problem, list_problems
from .results import public_view, totals

WORK_DIR = Path(os.environ.get("DOJO_WORK_DIR", REPO_ROOT / "work"))
WEB_DIST = REPO_ROOT / "web" / "dist"
HISTORY_FILE = ".dojo-history.jsonl"
EXTENSIONS = {"java": ".java", "python": ".py", "sql": ".sql"}
MAX_FILE_BYTES = 200_000
MODES = ("run", "submit")

from .coach.provider import load_env  # noqa: E402

load_env(REPO_ROOT / ".env")

app = FastAPI(title="DesignDojo", docs_url="/api/docs", openapi_url="/api/openapi.json")
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


# ------------------------------------------------------------------ helpers


def _problem(problem_id: str):
    try:
        return get_problem(problem_id)
    except ProblemError as e:
        raise HTTPException(404, str(e)) from None


def _lang(lang: str) -> str:
    if lang not in EXTENSIONS:
        raise HTTPException(404, f"unsupported language {lang!r}")
    return lang


def _workspace(problem_id: str, lang: str) -> Workspace:
    """Open the workspace, scaffolding it on first use; always refresh the generated contract."""
    problem, lang = _problem(problem_id), _lang(lang)
    if lang not in problem.langs:
        raise HTTPException(404, f"{problem.id} is solved in {', '.join(problem.langs)}")
    root = WORK_DIR / problem.track / f"{problem.id}-{lang}"
    legacy = WORK_DIR / f"{problem.id}-{lang}"  # before tracks: work/<id>-<lang>
    if legacy.is_dir() and not root.exists():
        root.parent.mkdir(parents=True, exist_ok=True)
        legacy.rename(root)
    scaffold(problem, lang, root)  # idempotent: rewrites contract/, keeps existing solution files
    return Workspace.open(root)


def _lock(ws: Workspace) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(str(ws.root), threading.Lock())


def _solution_path(ws: Workspace, rel: str) -> Path:
    """Validate a client-supplied path: must be solution/<...><ext>, no traversal."""
    p = PurePosixPath(rel)
    ext = EXTENSIONS[ws.lang]
    if (p.is_absolute() or ".." in p.parts or len(p.parts) < 2 or p.parts[0] != "solution"
            or p.suffix != ext or any(part.startswith(".") for part in p.parts)):
        raise HTTPException(400, f"files must live under solution/ and end in {ext}")
    full = (ws.root / p).resolve()
    if ws.solution_dir.resolve() not in full.parents:
        raise HTTPException(400, "path escapes the workspace")
    return full


def _files(ws: Workspace) -> list[dict]:
    out = []
    for sub, editable in (("solution", True), ("contract", False)):
        base = ws.root / sub
        for f in sorted(base.rglob(f"*{EXTENSIONS[ws.lang]}")):
            out.append({"path": f.relative_to(ws.root).as_posix(), "content": f.read_text(), "editable": editable})
    return out


# ------------------------------------------------------------------ problems


@app.get("/api/tracks")
def tracks():
    from .problems import TRACKS

    return [{"id": t, **info, "count": len(list_problems(t))} for t, info in TRACKS.items()]


@app.get("/api/problems")
def problems(track: str | None = None):
    from .problems import TRACKS

    if track is not None and track not in TRACKS:
        raise HTTPException(404, f"unknown track {track!r}")
    return [
        {
            "id": p.id,
            "title": p.title,
            "difficulty": p.meta.get("difficulty"),
            "category": p.meta.get("category", "Other"),
            "time_limit_min": p.meta.get("time_limit_min"),
            "tags": p.meta.get("tags", []),
            "track": p.track,
            "kind": p.kind,
            "langs": list(p.langs),
            "started": [lang for lang in p.langs
                        if (WORK_DIR / p.track / f"{p.id}-{lang}" / ".dojo.json").exists()
                        or (WORK_DIR / f"{p.id}-{lang}" / ".dojo.json").exists()],
        }
        for p in list_problems(track)
    ]


@app.get("/api/problems/{problem_id}")
def problem(problem_id: str):
    p = _problem(problem_id)
    return {
        "id": p.id,
        "title": p.title,
        "difficulty": p.meta.get("difficulty"),
        "time_limit_min": p.meta.get("time_limit_min"),
        "tags": p.meta.get("tags", []),
        "statement": p.statement,
        "track": p.track,
        "kind": p.kind,
        "langs": list(p.langs),
    }


# ------------------------------------------------------------------ workspace files


class FileBody(BaseModel):
    path: str
    content: str


class RenameBody(BaseModel):
    src: str
    dst: str


class PathBody(BaseModel):
    path: str


@app.get("/api/ws/{problem_id}/{lang}")
def workspace(problem_id: str, lang: str):
    ws = _workspace(problem_id, lang)
    if ws.problem.kind == "sql":
        from .sql.scaffold import entry_file

        entry = entry_file(ws.problem.sql_spec)
    else:
        entry = "solution/Solution.java" if lang == "java" else "solution/__init__.py"
    return {
        "root": str(ws.root), "entry": entry, "files": _files(ws),
        "level": ws.level, "curveballs_total": len(ws.problem.curveballs),
        "curveballs": [ws.problem.curveball_info(i) for i in range(1, ws.level + 1)],
    }


@app.post("/api/ws/{problem_id}/{lang}/curveball")
def next_curveball(problem_id: str, lang: str):
    from .curveballs import CurveballLocked, unlock_next

    ws = _workspace(problem_id, lang)
    lock = _lock(ws)
    if not lock.acquire(blocking=False):
        raise HTTPException(409, "a run is already in progress for this workspace")
    try:
        return unlock_next(ws)
    except CurveballLocked as e:
        raise HTTPException(409, str(e)) from None
    except JudgeError as e:
        raise HTTPException(500, str(e)) from None
    finally:
        lock.release()


@app.put("/api/ws/{problem_id}/{lang}/file")
def save_file(problem_id: str, lang: str, body: FileBody):
    ws = _workspace(problem_id, lang)
    if len(body.content.encode()) > MAX_FILE_BYTES:
        raise HTTPException(413, "file too large")
    path = _solution_path(ws, body.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.content)
    return {"ok": True}


@app.post("/api/ws/{problem_id}/{lang}/file")
def create_file(problem_id: str, lang: str, body: FileBody):
    ws = _workspace(problem_id, lang)
    path = _solution_path(ws, body.path)
    if path.exists():
        raise HTTPException(409, "file already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.content)
    return {"ok": True}


@app.post("/api/ws/{problem_id}/{lang}/rename")
def rename_file(problem_id: str, lang: str, body: RenameBody):
    ws = _workspace(problem_id, lang)
    src, dst = _solution_path(ws, body.src), _solution_path(ws, body.dst)
    if not src.exists():
        raise HTTPException(404, "no such file")
    if dst.exists():
        raise HTTPException(409, "target already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return {"ok": True}


@app.post("/api/ws/{problem_id}/{lang}/delete")
def delete_file(problem_id: str, lang: str, body: PathBody):
    ws = _workspace(problem_id, lang)
    path = _solution_path(ws, body.path)
    if not path.exists():
        raise HTTPException(404, "no such file")
    path.unlink()
    return {"ok": True}


@app.post("/api/ws/{problem_id}/{lang}/reset")
def reset(problem_id: str, lang: str):
    """Start over: move the current solution aside (never deleted) and re-create the stub."""
    ws = _workspace(problem_id, lang)
    backup = None
    if ws.solution_dir.exists():
        backups = ws.root / ".dojo-backups"
        backups.mkdir(exist_ok=True)
        backup = backups / time.strftime("solution-%Y%m%d-%H%M%S")
        shutil.move(str(ws.solution_dir), backup)
    scaffold(ws.problem, ws.lang, ws.root)
    return {"ok": True, "backup": str(backup) if backup else None}


# ------------------------------------------------------------------ judging


class JudgeBody(BaseModel):
    mode: str = "run"


@app.post("/api/ws/{problem_id}/{lang}/judge")
def run_judge(problem_id: str, lang: str, body: JudgeBody):
    if body.mode not in MODES:
        raise HTTPException(400, f"mode must be one of {list(MODES)}")
    ws = _workspace(problem_id, lang)
    lock = _lock(ws)
    if not lock.acquire(blocking=False):
        raise HTTPException(409, "a run is already in progress for this workspace")
    try:
        t0 = time.monotonic()
        raw = judge(ws, ws.suites if body.mode == "submit" else ["sample"])
        elapsed = round(time.monotonic() - t0, 2)
    except JudgeError as e:
        raise HTTPException(500, str(e)) from None
    finally:
        lock.release()
    if body.mode == "submit":
        from .coach import latest
        from .curveballs import evaluate

        rev = latest(ws)
        design = rev["review"].get("design_score") if rev and rev.get("meta", {}).get("source") == "ai" \
            and rev.get("review") else None
        result = evaluate(ws, raw, design)
    else:
        result = public_view(raw)
    passed, total = totals(result)
    entry = {
        "id": uuid.uuid4().hex[:10],
        "at": time.time(),
        "mode": body.mode,
        "status": result.get("status"),
        "passed": passed,
        "total": total,
        "seconds": elapsed,
        "result": result,
    }
    with (ws.root / HISTORY_FILE).open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


class AnswersBody(BaseModel):
    answers: dict[str, str]


def _sql_ws(problem_id: str, lang: str) -> Workspace:
    ws = _workspace(problem_id, lang)
    if ws.problem.kind != "sql":
        raise HTTPException(404, "interview questions are part of the database-design track")
    return ws


@app.get("/api/ws/{problem_id}/{lang}/questions")
def questions(problem_id: str, lang: str):
    from .sql.questions import public_questions, read_answers

    ws = _sql_ws(problem_id, lang)
    return {"questions": public_questions(ws.problem), "answers": read_answers(ws.root)}


@app.put("/api/ws/{problem_id}/{lang}/answers")
def save_answers_api(problem_id: str, lang: str, body: AnswersBody):
    from .sql.questions import load_questions, save_answers

    ws = _sql_ws(problem_id, lang)
    known = {q["id"] for q in load_questions(ws.problem)}
    save_answers(ws.root, {k: v for k, v in body.answers.items() if k in known})
    return {"ok": True}


class GradeBody(BaseModel):
    force: bool = False


@app.post("/api/ws/{problem_id}/{lang}/answers/grade")
def grade_answers(problem_id: str, lang: str, body: GradeBody):
    from .sql.questions import grade

    ws = _sql_ws(problem_id, lang)
    lock = _lock(ws)
    if not lock.acquire(blocking=False):
        raise HTTPException(409, "something else is running for this workspace")
    try:
        return grade(ws, force=body.force)
    finally:
        lock.release()


class ConsoleBody(BaseModel):
    sql: str
    scenario: str | None = None


@app.get("/api/ws/{problem_id}/{lang}/console")
def console_info(problem_id: str, lang: str):
    from .sql.console import scenarios

    ws = _workspace(problem_id, lang)
    if ws.problem.kind != "sql":
        raise HTTPException(404, "the SQL console is for database-design problems")
    return {"scenarios": scenarios(ws)}


@app.post("/api/ws/{problem_id}/{lang}/console")
def console_run(problem_id: str, lang: str, body: ConsoleBody):
    from .sql.console import run_console

    ws = _workspace(problem_id, lang)
    if ws.problem.kind != "sql":
        raise HTTPException(404, "the SQL console is for database-design problems")
    try:
        return run_console(ws, body.sql, body.scenario)
    except JudgeError as e:
        raise HTTPException(500, str(e)) from None


@app.get("/api/ws/{problem_id}/{lang}/history")
def history(problem_id: str, lang: str, limit: int = 30):
    ws = _workspace(problem_id, lang)
    path = ws.root / HISTORY_FILE
    if not path.exists():
        return []
    entries = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return list(reversed(entries))[:limit]


@app.get("/api/ws/{problem_id}/{lang}/analysis")
def analysis(problem_id: str, lang: str):
    from .analyzer import analyze

    ws = _workspace(problem_id, lang)
    return analyze(ws.root, ws.lang, concurrency=ws.problem.concurrency, contract_types=ws.problem.contract_types)


class ReviewBody(BaseModel):
    force: bool = False


def _last_run(ws: Workspace) -> dict | None:
    path = ws.root / HISTORY_FILE
    if not path.exists():
        return None
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else None


@app.post("/api/ws/{problem_id}/{lang}/review")
def coach_review(problem_id: str, lang: str, body: ReviewBody):
    from .coach import CoachError, CoachUnavailable, review

    ws = _workspace(problem_id, lang)
    lock = _lock(ws)
    if not lock.acquire(blocking=False):
        raise HTTPException(409, "a run or review is already in progress for this workspace")
    try:
        return review(ws, last_run=_last_run(ws), force=body.force)
    except CoachError as e:
        raise HTTPException(503, str(e)) from None
    except CoachUnavailable as e:
        raise HTTPException(429, str(e)) from None
    finally:
        lock.release()


@app.get("/api/ws/{problem_id}/{lang}/review")
def coach_latest(problem_id: str, lang: str):
    from .coach import latest

    return latest(_workspace(problem_id, lang)) or {"review": None}


@app.get("/api/coach/status")
def coach_status():
    from .coach.provider import CoachError, default_provider

    try:
        p = default_provider()
    except CoachError as e:
        return {"configured": False, "message": str(e)}
    return {"configured": True, "provider": p.name, **p.usage_today()}


# ------------------------------------------------------------------ web UI


if WEB_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        candidate = (WEB_DIST / path).resolve()
        if path and WEB_DIST.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")
