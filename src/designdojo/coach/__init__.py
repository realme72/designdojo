"""The design coach: analysis + problem rubric -> LLM -> validated, line-anchored review."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from pathlib import Path

from ..analyzer import analyze
import httpx

from .offline import offline_review
from .prompt import MAX_COMMENTS, MAX_OUTPUT_TOKENS, PROMPT_VERSION, SYSTEM, build, read_solution
from .provider import CoachError, CoachUnavailable, Provider, default_provider

__all__ = ["review", "latest", "validate", "CoachError", "CoachUnavailable"]

log = logging.getLogger("designdojo.coach")

EXT = {"java": ".java", "python": ".py"}
KINDS = {"suggestion", "praise", "warning", "overengineering"}
DP_STATUS = {"good", "partial", "missed", "not_applicable"}
CACHE_DIR = ".dojo-cache/coach"


def _s(v, limit: int) -> str | None:
    if v is None or (isinstance(v, str) and v.strip().lower() in ("", "null", "none", "n/a")):
        return None
    return str(v).strip()[:limit]


def validate(raw: dict, files: dict[str, str], dp_ids: list[str]) -> tuple[dict, int]:
    """Coerce model output into the review schema. Comments that don't point at real
    solution lines are dropped (returned count), never 'fixed up' into wrong places."""
    line_counts = {p: max(1, len(src.splitlines())) for p, src in files.items()}
    by_base = {p.split("/")[-1]: p for p in files}
    comments, dropped = [], 0
    for c in raw.get("comments") or []:
        if not isinstance(c, dict):
            dropped += 1
            continue
        f = str(c.get("file") or "")
        f = f if f in line_counts else ("solution/" + f if "solution/" + f in line_counts else by_base.get(f.split("/")[-1]))
        try:
            start = int(c.get("line_start"))
            end = int(c.get("line_end") or start)
        except (TypeError, ValueError):
            dropped += 1
            continue
        if f is None or not (1 <= start <= line_counts[f]):
            dropped += 1
            continue
        end = min(max(end, start), line_counts[f])
        hints = [h for h in (_s(h, 400) for h in (c.get("hints") or []) if isinstance(c.get("hints"), list)) if h][:3]
        if not hints:
            dropped += 1
            continue
        kind = c.get("kind") if c.get("kind") in KINDS else "suggestion"
        try:
            conf = min(1.0, max(0.0, float(c.get("confidence", 0.6))))
        except (TypeError, ValueError):
            conf = 0.6
        dp = c.get("decision_point")
        comments.append({
            "file": f, "line_start": start, "line_end": end, "kind": kind,
            "principle": _s(c.get("principle"), 60), "pattern": _s(c.get("pattern"), 60),
            "decision_point": dp if dp in dp_ids else None,
            "title": _s(c.get("title"), 120) or "Design note",
            "hints": hints,
            "example": _s(c.get("example"), 1500),
            "why_here": _s(c.get("why_here"), 500),
            "confidence": round(conf, 2),
        })
    comments = comments[:MAX_COMMENTS]

    seen = {}
    for d in raw.get("decision_points") or []:
        if isinstance(d, dict) and d.get("id") in dp_ids and d["id"] not in seen:
            seen[d["id"]] = {"id": d["id"], "status": d.get("status") if d.get("status") in DP_STATUS else "partial",
                             "note": _s(d.get("note"), 300)}
    decisions = [seen.get(i, {"id": i, "status": "not_assessed", "note": None}) for i in dp_ids]

    try:
        score = int(raw.get("design_score"))
        score = min(100, max(0, score))
    except (TypeError, ValueError):
        score = None
    return {"summary": _s(raw.get("summary"), 800) or "", "design_score": score,
            "decision_points": decisions, "comments": comments}, dropped


def _parse_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    try:
        return json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            raise CoachUnavailable("The model did not return JSON.") from None
        try:
            return json.loads(m.group(0))
        except ValueError:
            raise CoachUnavailable("The model returned malformed JSON.") from None


def _tests_summary(history_entry: dict | None) -> str:
    if not history_entry:
        return "not run yet"
    r = history_entry.get("result") or {}
    if r.get("status") != "ok":
        return f"last run: {r.get('status', '?').replace('_', ' ')}"
    parts = []
    for s in r.get("suites", []):
        failing = [c["name"] for c in s["cases"] if c["status"] != "pass"]
        parts.append(f"{s['name']} {s['passed']}/{s['total']}" + (f" (failing: {', '.join(failing[:6])})" if failing else ""))
    return f"last {history_entry.get('mode', 'run')}: " + "; ".join(parts)


def _offline_reason(e: Exception) -> str:
    text = str(e)
    if isinstance(e, CoachError) and "not set" in text:
        return "AI coach not configured"
    if "daily limit" in text or "per day" in text.lower():
        return "Groq daily limit reached; it resets at 00:00 UTC (05:30 IST)"
    if "rate limited" in text:
        return "Groq is rate-limiting right now; try the AI coach again in a minute"
    if isinstance(e, httpx.HTTPError):
        return "couldn't reach Groq"
    return "AI coach unavailable"


def _tests_note(last_run: dict | None) -> str:
    r = (last_run or {}).get("result") or {}
    for s in r.get("suites", []):
        if s["name"] == "concurrency" and s["passed"] < s["total"]:
            return "Your last submit fails race scenarios, so start with the thread-safety comments."
    return ""


def review(ws, *, last_run: dict | None = None, provider: Provider | None = None, force: bool = False,
           allow_offline: bool = True) -> dict:
    """Review a workspace. Cached by prompt content, so an unchanged design costs nothing.
    If the AI coach can't run (no key, daily limit, network), falls back to an offline review
    built from static analysis, clearly labelled as such and never cached as an AI review."""
    problem, lang = ws.problem, ws.lang
    files = read_solution(ws.root, EXT[lang])
    analysis = analyze(ws.root, lang, concurrency=problem.concurrency, contract_types=problem.contract_types)
    dps = problem.decision_points
    from ..judge import problem_text

    user, meta = build(title=problem.title, statement=problem_text(problem, ws.level), decision_points=dps,
                       analysis=analysis, files=files, tests=_tests_summary(last_run))

    key = hashlib.sha256(f"{PROMPT_VERSION}\n{SYSTEM}\n{user}".encode()).hexdigest()[:24]
    cache = ws.root / CACHE_DIR
    cached = cache / f"{key}.json"
    if cached.exists() and not force:
        out = json.loads(cached.read_text())
        out["meta"]["cached"] = True
        _write_latest(cache, out)
        return out

    t0 = time.monotonic()
    try:
        provider = provider or default_provider()
        completion = provider.complete(SYSTEM, user, MAX_OUTPUT_TOKENS)
        raw = _parse_json(completion.text)
    except (CoachError, CoachUnavailable, httpx.HTTPError) as e:
        if not allow_offline:
            raise
        log.info("AI coach unavailable, using offline review: %s", e)
        reason = _offline_reason(e)
        out = {
            "review": offline_review(analysis, files, dps, reason=reason, tests_note=_tests_note(last_run)),
            "meta": {**meta, "source": "offline", "reason": reason, "detail": str(e)[:500],
                     "model": "static analysis", "provider": "offline", "prompt_tokens": 0,
                     "completion_tokens": 0, "dropped_comments": 0, "seconds": round(time.monotonic() - t0, 1),
                     "at": time.time(), "cached": False, "key": f"offline-{key}"},
        }
        _write_latest(ws.root / CACHE_DIR, out)
        return out
    rev, dropped = validate(raw, files, [d["id"] for d in dps])
    out = {
        "review": rev,
        "meta": {
            **meta, "source": "ai", "model": completion.model, "provider": getattr(provider, "name", "?"),
            "prompt_tokens": completion.prompt_tokens, "completion_tokens": completion.completion_tokens,
            "dropped_comments": dropped, "seconds": round(time.monotonic() - t0, 1),
            "at": time.time(), "cached": False, "key": key,
        },
    }
    cache.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(out))
    _write_latest(cache, out)
    return out


def _write_latest(cache: Path, out: dict) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "latest.json").write_text(json.dumps(out))


def latest(ws) -> dict | None:
    p = ws.root / CACHE_DIR / "latest.json"
    return json.loads(p.read_text()) if p.exists() else None
