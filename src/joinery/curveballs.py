"""Curveball lifecycle: unlock (gated on a fully passing submit), snapshots, churn, scoring."""

from __future__ import annotations

import shutil
from pathlib import Path

from .analyzer.churn import churn
from .judge import JudgeError, Workspace, judge, scaffold
from .results import public_view, totals

SNAPSHOTS = ".joinery-snapshots"

WEIGHTS = {"correctness": 35, "concurrency": 15, "extensibility": 25, "design": 25}


class CurveballLocked(JudgeError):
    """The current level isn't fully passing yet, or there are no more curveballs."""


def snapshot_dir(ws: Workspace, level: int) -> Path:
    """Code as it was when curveball `level` was unlocked (i.e. the solution to level-1)."""
    return ws.root / SNAPSHOTS / str(level)


def unlock_next(ws: Workspace) -> dict:
    total = len(ws.problem.curveballs)
    if ws.level >= total:
        raise CurveballLocked("no more curveballs for this problem" if total else "this problem has no curveballs yet")
    result = judge(ws, ws.suites)
    passed, count = totals(result)
    if result.get("status") != "ok" or passed != count:
        raise CurveballLocked(f"pass every scenario first ({passed}/{count} passing)")
    snap = snapshot_dir(ws, ws.level + 1)
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(ws.solution_dir, snap / "solution")
    scaffold(ws.problem, ws.lang, ws.root, level=ws.level + 1)
    return ws.problem.curveball_info(ws.level + 1)


def churn_report(ws: Workspace) -> list[dict]:
    """Churn for each unlocked curveball: snapshot k -> snapshot k+1 (or the current code for the last)."""
    out = []
    for k in range(1, ws.level + 1):
        before = snapshot_dir(ws, k)
        after = snapshot_dir(ws, k + 1) if k < ws.level else ws.root
        if not (before / "solution").is_dir():
            continue
        try:
            c = churn(before, after, ws.lang)
        except (SyntaxError, ValueError) as e:  # code that doesn't parse: no churn, no crash
            c = {"error": f"could not analyze: {e}", "extensibility": 0.0}
        out.append({"curveball": k, "title": ws.problem.curveball_info(k)["title"], **c})
    return out


def _ratio(result: dict, names: set[str]) -> tuple[float, int] | None:
    suites = [s for s in result.get("suites", []) if s["name"] in names and s["total"]]
    total = sum(s["total"] for s in suites)
    return (sum(s["passed"] for s in suites) / total, total) if total else None


def score(result: dict, churns: list[dict], design_score: int | None) -> dict:
    """Spec §9. Components that don't apply are excluded and the rest re-weighted."""
    comps = []
    if result.get("status") != "ok":
        return {"total": 0, "components": [{"name": "correctness", "weight": 100, "points": 0,
                                            "detail": result.get("status", "").replace("_", " ")}]}
    r = _ratio(result, {"sample", "hidden"})
    comps.append({"name": "correctness", "weight": WEIGHTS["correctness"],
                  "points": round(r[0] * WEIGHTS["correctness"], 1) if r else 0,
                  "detail": f"{round(r[0] * 100)}% of sample + hidden" if r else "no scenarios"})
    c = _ratio(result, {"concurrency"})
    comps.append({"name": "concurrency", "weight": WEIGHTS["concurrency"] if c else 0,
                  "points": round(c[0] * WEIGHTS["concurrency"], 1) if c else None,
                  "detail": f"{round(c[0] * 100)}% of race scenarios" if c else "not a concurrency problem"})
    if churns:
        per = []
        for ch in churns:
            cb = _ratio(result, {f"curveball-{ch['curveball']}"})
            per.append((cb[0] if cb else 0) * ch.get("extensibility", 0))
        ext = sum(per) / len(per)
        comps.append({"name": "extensibility", "weight": WEIGHTS["extensibility"],
                      "points": round(ext * WEIGHTS["extensibility"], 1),
                      "detail": f"{len(churns)} curveball(s): pass rate × how little existing code changed"})
    else:
        comps.append({"name": "extensibility", "weight": 0, "points": None,
                      "detail": "unlock a curveball to measure this"})
    if design_score is not None:
        comps.append({"name": "design", "weight": WEIGHTS["design"],
                      "points": round(design_score / 100 * WEIGHTS["design"], 1),
                      "detail": f"coach design score {design_score}/100"})
    else:
        comps.append({"name": "design", "weight": 0, "points": None, "detail": "run an AI design review to include this"})
    weight = sum(x["weight"] for x in comps)
    points = sum(x["points"] or 0 for x in comps)
    return {"total": round(points / weight * 100) if weight else 0, "components": comps}


def evaluate(ws: Workspace, raw_result: dict, design_score: int | None) -> dict:
    """Public result + churn + score for a full submit."""
    result = public_view(raw_result)
    churns = churn_report(ws)
    result["churn"] = churns
    result["score"] = score(result, churns, design_score)
    return result
