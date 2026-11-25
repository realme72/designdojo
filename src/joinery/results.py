"""What a solver is allowed to see of a judge result.

Hidden suites are stripped here, on the server, so details never reach the
browser (or the terminal) at all. Everything user-facing goes through public_view().
"""

from __future__ import annotations

import copy

from .problems import VISIBLE_SUITES

# Failure kinds whose message is about the solver's code, not the test inputs.
SAFE_MESSAGE_KINDS = {"harness_error", "missing_entrypoint", "missing_method", "timeout", "skipped"}
KEEP_FIELDS = {"name", "status", "kind", "iteration", "repeat", "ms"}


def _short_exception(msg: str) -> str:
    """'park threw IllegalStateException: x at Lot.java:12' -> 'threw IllegalStateException: x at Lot.java:12'."""
    _, sep, rest = msg.partition(" threw ")
    return f"threw {rest}" if sep else msg


def public_view(result: dict) -> dict:
    out = copy.deepcopy(result)
    for suite in out.get("suites") or []:
        visible = suite["name"] in VISIBLE_SUITES
        suite["visible"] = visible
        if visible:
            continue
        for i, case in enumerate(suite["cases"]):
            if case["status"] == "pass":
                continue
            masked = {k: v for k, v in case.items() if k in KEEP_FIELDS}
            kind = case.get("kind")
            if kind in SAFE_MESSAGE_KINDS:
                masked["message"] = case.get("message", "")
            elif kind == "unexpected_error":
                masked["message"] = _short_exception(case.get("message", ""))
            suite["cases"][i] = masked
    return out


def totals(result: dict) -> tuple[int, int]:
    suites = result.get("suites") or []
    return sum(s["passed"] for s in suites), sum(s["total"] for s in suites)
