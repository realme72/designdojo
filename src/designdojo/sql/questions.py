"""Interview questions for database-design problems: the things an interviewer ASKS
("RDBMS or NoSQL, and why?", "how do you stop overselling?"), answered in prose.

questions.yaml (per problem):
    - id: storage_choice
      stage: before | design | after       # when an interviewer would ask it
      question: Would you use a relational database or a NoSQL store here? Why?
      points:                              # what a strong answer covers (the rubric)
        - text: Orders, lines and stock must change together atomically (ACID transactions)
          keywords: [acid, transaction, atomic]
      follow_up: What would push you towards NoSQL for part of this system?

Answers live in the workspace (answers.json). Grading uses the AI coach; if it is
unavailable, an offline keyword check marks points as "probably mentioned", clearly labelled
as a heuristic that can't judge reasoning.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import yaml

ANSWERS_FILE = "answers.json"
CACHE_DIR = ".dojo-cache/answers"
STAGES = ("before", "design", "after")
MAX_ANSWER_CHARS = 2500

SYSTEM = """You are a senior engineer running a database-design interview. The candidate answered
your questions in writing. Grade EACH answer against its rubric points: a point is "covered" only if
the answer states the idea or clearly implies it with correct reasoning; naming a buzzword without
the reason is "partial". Reward correct reasoning that the rubric doesn't list (mention it in
feedback). Be direct, specific to this problem, and kind. Never invent what the candidate said.

Reply with ONE JSON object, no prose:
{"answers": [{"id": "<question id>",
              "verdict": "strong|partial|weak|missing",
              "covered": [<indexes of rubric points covered>],
              "partial": [<indexes partially covered>],
              "feedback": "<= 3 sentences: what was good, what is missing or wrong, and why it matters here",
              "follow_up": "one probing follow-up question an interviewer would ask next"}],
 "summary": "<= 2 sentences overall"}"""


def load_questions(problem) -> list[dict]:
    path = problem.root / "questions.yaml"
    if not path.exists():
        return []
    qs = yaml.safe_load(path.read_text()) or []
    for q in qs:
        q.setdefault("stage", "design")
        q["points"] = [p if isinstance(p, dict) else {"text": p, "keywords": []} for p in q.get("points") or []]
    return qs


def public_questions(problem) -> list[dict]:
    """What the learner sees up front: the question, never the rubric."""
    return [{"id": q["id"], "stage": q["stage"], "question": q["question"], "points": len(q["points"])}
            for q in load_questions(problem)]


def lint_questions(problem) -> list[str]:
    issues = []
    try:
        qs = load_questions(problem)
    except Exception as e:  # noqa: BLE001
        return [f"questions.yaml: {e}"]
    if not qs:
        return ["questions.yaml: missing or empty (interview questions are part of every DB problem)"]
    seen = set()
    for q in qs:
        where = f"questions.yaml {q.get('id', '?')}"
        for k in ("id", "question", "points"):
            if not q.get(k):
                issues.append(f"{where}: missing {k}")
        if q.get("id") in seen:
            issues.append(f"{where}: duplicate id")
        seen.add(q.get("id"))
        if q["stage"] not in STAGES:
            issues.append(f"{where}: stage must be one of {STAGES}")
        for p in q["points"]:
            if not p.get("text"):
                issues.append(f"{where}: point without text")
    return issues


def read_answers(root: Path) -> dict[str, str]:
    p = Path(root) / ANSWERS_FILE
    try:
        data = json.loads(p.read_text()) if p.exists() else {}
    except ValueError:
        return {}
    return {k: v for k, v in (data.get("answers") or {}).items() if isinstance(v, str)}


def save_answers(root: Path, answers: dict[str, str]) -> None:
    p = Path(root) / ANSWERS_FILE
    clean = {k: str(v)[:MAX_ANSWER_CHARS] for k, v in answers.items()}
    tmp = p.with_name(f".{p.name}.tmp")
    tmp.write_text(json.dumps({"answers": clean}, indent=2) + "\n")
    tmp.replace(p)


def _offline(qs: list[dict], answers: dict[str, str], reason: str) -> dict:
    out = []
    for q in qs:
        text = (answers.get(q["id"]) or "").lower()
        if not text.strip():
            out.append({"id": q["id"], "verdict": "missing", "covered": [], "partial": [],
                        "feedback": "Not answered yet.", "follow_up": None})
            continue
        hit = [i for i, p in enumerate(q["points"])
               if any(re.search(("\\b" if k[:1].isalnum() else "") + re.escape(k.lower()), text)
                      for k in p.get("keywords") or [])]
        ratio = len(hit) / max(1, len(q["points"]))
        out.append({
            "id": q["id"],
            "verdict": "unassessed",
            "covered": [],
            "partial": hit,  # keyword hits are only "probably mentioned", never "covered"
            "feedback": (f"Keyword check only ({reason}): {len(hit)} of {len(q['points'])} key ideas seem to be "
                         "mentioned. It can't judge whether your reasoning is right; reveal the key points "
                         "and compare." if ratio else
                         f"Keyword check only ({reason}): none of the key ideas' usual terms appear. "
                         "Reveal the key points and compare."),
            "follow_up": q.get("follow_up"),
        })
    return {"answers": out, "summary": f"Offline keyword check ({reason}); the AI coach grades reasoning.",
            "source": "offline"}


def _user_prompt(problem, qs: list[dict], answers: dict[str, str]) -> str:
    from ..coach.prompt import requirements

    parts = [f"PROBLEM: {problem.title}\nREQUIREMENTS:\n{requirements(problem.statement, 1800)}\n"]
    for q in qs:
        rubric = "\n".join(f"  [{i}] {p['text']}" for i, p in enumerate(q["points"]))
        ans = (answers.get(q["id"]) or "").strip() or "(no answer)"
        parts.append(f"QUESTION {q['id']}: {q['question']}\nRUBRIC:\n{rubric}\nCANDIDATE ANSWER:\n{ans[:1500]}\n")
    return "\n".join(parts)


def grade(ws, *, force: bool = False) -> dict:
    """Grade the workspace's answers. Cached by content; offline fallback when the AI is unavailable."""
    import httpx

    from ..coach import _offline_reason, _parse_json
    from ..coach.provider import CoachError, CoachUnavailable, default_provider

    problem = ws.problem
    qs = load_questions(problem)
    answers = read_answers(ws.root)
    answered = [q for q in qs if (answers.get(q["id"]) or "").strip()]
    if not answered:
        return {"answers": [], "summary": "Answer at least one question first.", "source": "none"}
    user = _user_prompt(problem, answered, answers)
    key = hashlib.sha256(f"{SYSTEM}\n{user}".encode()).hexdigest()[:24]
    cache = Path(ws.root) / CACHE_DIR
    cached = cache / f"{key}.json"
    if cached.exists() and not force:
        out = json.loads(cached.read_text())
        out["cached"] = True
        return out
    t0 = time.monotonic()
    try:
        completion = default_provider().complete(SYSTEM, user, 1600)
        raw = _parse_json(completion.text)
    except (CoachError, CoachUnavailable, httpx.HTTPError) as e:
        out = _offline(answered, answers, _offline_reason(e))
        out["questions"] = _reveal(answered)
        return out
    by_id = {a.get("id"): a for a in raw.get("answers") or [] if isinstance(a, dict)}
    graded = []
    for q in answered:
        a = by_id.get(q["id"]) or {}
        n = len(q["points"])
        idx = lambda xs: sorted({int(i) for i in xs or [] if str(i).isdigit() and 0 <= int(i) < n})  # noqa: E731
        verdict = a.get("verdict") if a.get("verdict") in ("strong", "partial", "weak", "missing") else "partial"
        graded.append({"id": q["id"], "verdict": verdict, "covered": idx(a.get("covered")),
                       "partial": [i for i in idx(a.get("partial")) if i not in idx(a.get("covered"))],
                       "feedback": str(a.get("feedback") or "")[:600],
                       "follow_up": str(a.get("follow_up") or q.get("follow_up") or "")[:300] or None})
    out = {"answers": graded, "summary": str(raw.get("summary") or "")[:400], "source": "ai",
           "model": completion.model, "seconds": round(time.monotonic() - t0, 1),
           "questions": _reveal(answered), "cached": False}
    cache.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(out))
    return out


def _reveal(qs: list[dict]) -> dict[str, list[str]]:
    """Rubric points, sent only with feedback (after the learner has committed to an answer)."""
    return {q["id"]: [p["text"] for p in q["points"]] for q in qs}
