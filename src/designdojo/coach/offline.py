"""Offline coach: turns static-analysis signals into coach-shaped comments, no LLM needed.

Used when the AI coach is unavailable (Groq daily limit, no key, network). It is honest
about what it is: it can only comment where the parser found something, it never invents
a design score, and decision points without signals are "not assessed", never "good".
"""

from __future__ import annotations

import re

# smell id -> (kind, title, principle, pattern, [nudge, principle, shape]) ; {sym} / {ev} interpolated
TEMPLATES: dict[str, tuple[str, str, str | None, str | None, list[str]]] = {
    "TYPE_SWITCH": (
        "suggestion", "Behaviour chosen by branching on a kind", "Open/Closed", "Strategy",
        ["What would you have to edit here to support one more kind?",
         "Each new kind means editing this branch: Open/Closed says new behaviour should be new code.",
         "Move each branch behind a common interface (a strategy, or a data table if it's pure data) "
         "and pick it once, in the composition root."],
    ),
    "STATE_FLAG": (
        "suggestion", "Status flag drives the behaviour", None, "State",
        ["How many methods change behaviour when `{sym}` changes?",
         "A flag that is both branched on and reassigned across methods is an implicit state machine.",
         "Make each state an object with the same interface; transitions return the next state."],
    ),
    "NEW_IN_LOGIC": (
        "suggestion", "Collaborator created inside business logic", "Dependency Inversion", None,
        ["Could you test {sym} with a fake of what it creates here?",
         "Creating a concrete collaborator inline hard-wires it: high-level code depends on a low-level detail.",
         "Accept the collaborator (or a factory) through the constructor and build it in the composition root."],
    ),
    "DIRECT_TIME": (
        "warning", "Reads the system clock directly", "Dependency Inversion", None,
        ["How would a test make one hour pass instantly here?",
         "The problem injects a Clock so time is controllable; reading the system clock bypasses it.",
         "Use the injected clock everywhere time is needed."],
    ),
    "GOD_CLASS": (
        "suggestion", "One class doing several jobs", "Single Responsibility", None,
        ["If you had to describe `{sym}` in one sentence, would it need an 'and'?",
         "Groups of methods that share no fields are separate responsibilities living in one class.",
         "Split along those groups into collaborating classes, and keep this one as the coordinator."],
    ),
    "TELESCOPING_CTOR": (
        "suggestion", "Constructor with many parameters", None, "Builder",
        ["Can a caller tell which argument is which without the signature open?",
         "Long parameter lists are easy to misorder and hard to extend.",
         "Group related values into a parameter object, or use a builder for optional parts."],
    ),
    "GLOBAL_STATE": (
        "warning", "Shared mutable state outside any instance", None, None,
        ["What happens to `{sym}` if two lots exist, or two tests run?",
         "Global or class-level mutable state is shared by every instance and every thread.",
         "Make it instance state and pass it where it's needed."],
    ),
    "REFUSED_BEQUEST": (
        "warning", "Inherited method that refuses to work", "Liskov Substitution", None,
        ["Can every caller of the parent type safely call `{sym}`?",
         "A subtype that throws on an inherited method breaks substitutability.",
         "Narrow the interface (split it) or use composition instead of inheritance."],
    ),
    "FAT_INTERFACE": (
        "suggestion", "Interface with many methods", "Interface Segregation", None,
        ["Does every implementer need all of `{sym}`'s methods?",
         "Clients shouldn't depend on methods they don't use.",
         "Split it into smaller role interfaces."],
    ),
    "UNGUARDED_SHARED": (
        "warning", "Shared state changed without a lock", "Thread safety", None,
        ["What happens if two threads run this at the same moment?",
         "{ev}. Check-then-act sequences on shared state can interleave between threads.",
         "Guard each read-modify-write with one lock (keep it short), or use atomic/concurrent structures."],
    ),
    "SPECULATIVE_PATTERN": (
        "overengineering", "Abstraction that may not be needed yet", None, None,
        ["What second implementation of `{sym}` do you expect?",
         "Indirection costs reading time; it pays off only where variation is likely.",
         "Keep it if this is a real axis of change in the problem; otherwise inline it."],
    ),
}

WORD = re.compile(r"[a-z]{3,}")
STOP = {"the", "and", "how", "what", "self", "this", "return", "def", "for", "with", "int", "str", "new"}


def _words(text: str) -> set[str]:
    words = set()
    for w in WORD.findall(re.sub(r"([a-z])([A-Z])", r"\1 \2", text).lower().replace("_", " ")):
        words.add(w.rstrip("s"))
    return words - STOP


def _exact(text: str) -> set[str]:
    """Identifier parts, lowercased, unstemmed: hourly_rate_cents -> {hourly, rate, cents}."""
    return {w.lower() for w in re.findall(r"[A-Za-z][a-z]+|[A-Z]+(?![a-z])", text)}


def _pick_dp(smell: dict, code: str, dps: list[dict]) -> dict | None:
    """Decision point whose smells include this one and whose wording best matches the code."""
    candidates = [d for d in dps if smell["id"] in (d.get("smells") or [])]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    words = _words(code + " " + smell["evidence"])
    exact = _exact(code)

    def score(d: dict) -> int:
        keywords = {k.lower() for k in d.get("keywords") or []}
        return 3 * len(exact & keywords) + len(words & _words(f"{d['id']} {d['question']} {d['good']}"))

    return max((score(d), -i, d) for i, d in enumerate(candidates))[2]


def offline_review(analysis: dict, files: dict[str, str], dps: list[dict], *, reason: str,
                   tests_note: str = "") -> dict:
    comments = []
    hit: dict[str, list[str]] = {}   # warnings: the decision was likely missed
    soft: dict[str, list[str]] = {}  # info: worth a look, not a verdict
    for s in analysis["smells"]:
        tpl = TEMPLATES.get(s["id"])
        if tpl is None or s["file"] not in files:
            continue
        kind, title, principle, pattern, hints = tpl
        lines = files[s["file"]].splitlines()
        code = "\n".join(lines[s["line_start"] - 1: s["line_end"]])
        dp = _pick_dp(s, code, dps)
        sym = s["symbol"].split(".")[-1]
        info = s["level"] == "info"
        if dp:
            (soft if info else hit).setdefault(dp["id"], []).append(s["title"].lower())
        comments.append({
            "file": s["file"], "line_start": s["line_start"], "line_end": s["line_end"],
            "kind": kind, "principle": principle, "pattern": pattern,
            "decision_point": dp["id"] if dp else None,
            "title": f"{title}: {s['evidence']}" if len(s["evidence"]) < 70 else title,
            "hints": [h.format(sym=sym, ev=s["evidence"].rstrip(".")) for h in hints],
            "example": None,
            "why_here": (f"In this problem, good looks like: {dp['good']}" if dp else None),
            "confidence": 0.35 if info else 0.7,
        })

    decisions = []
    for d in dps:
        if d["id"] in hit:
            decisions.append({"id": d["id"], "status": "missed",
                              "note": "Signals here: " + ", ".join(sorted(set(hit[d["id"]]))) + "."})
        elif d["id"] in soft:
            decisions.append({"id": d["id"], "status": "not_assessed",
                              "note": "Worth a look: " + ", ".join(sorted(set(soft[d["id"]]))) + "."})
        else:
            decisions.append({"id": d["id"], "status": "not_assessed",
                              "note": "No static signals. Only the AI coach can judge this one."})

    warnings = sum(1 for s in analysis["smells"] if s["level"] == "warning")
    summary = (f"Offline review from static analysis ({reason}). "
               + (f"{warnings} thing(s) could be better; each comment below says what and why."
                  if warnings else "No design problems detected by the parser. That's a good sign, "
                                   "but it can't judge everything the AI coach would.")
               + (f" {tests_note}" if tests_note else ""))
    # warnings first, low-confidence notes last
    comments.sort(key=lambda c: (c["kind"] != "warning", c["confidence"] < 0.5, c["file"], c["line_start"]))
    return {"summary": summary, "design_score": None, "decision_points": decisions, "comments": comments}
