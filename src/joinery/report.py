"""Human-readable terminal rendering of judge results."""

from __future__ import annotations

import json
import os
import sys

from .results import public_view, totals

_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

KIND_LABELS = {
    "wrong_result": "wrong result",
    "expected_error": "missing/incorrect error",
    "unexpected_error": "unexpected exception",
    "assertion": "invariant violated",
    "timeout": "timeout",
    "missing_entrypoint": "entry point missing",
    "missing_method": "method missing",
    "harness_error": "harness error",
    "skipped": "skipped",
}

__all__ = ["render", "totals", "KIND_LABELS"]


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def green(s): return _c("32", s)
def red(s): return _c("31", s)
def yellow(s): return _c("33", s)
def dim(s): return _c("2", s)
def bold(s): return _c("1", s)


def render(raw: dict, title: str, lang: str) -> str:
    result = public_view(raw)
    out = [bold(f"{title} · {lang}"), ""]
    status = result.get("status")
    if status == "compile_error":
        out.append(red("✗ Does not compile"))
        for d in result.get("diagnostics", []):
            loc = f"{d['file']}:{d['line']}" if d.get("file") else "?"
            out.append(f"  {loc}  {d['message']}")
        return "\n".join(out)
    if status != "ok":
        out.append(red(f"✗ {status}"))
        out.append(result.get("message", ""))
        return "\n".join(out)

    for suite in result["suites"]:
        name, passed, total = suite["name"], suite["passed"], suite["total"]
        mark = green("✓") if passed == total else red("✗")
        out.append(f"  {name:<12} {passed:>3}/{total:<3} {mark}")
        for case in suite["cases"]:
            if case["status"] == "pass":
                continue
            label = KIND_LABELS.get(case.get("kind", ""), case.get("kind", "failed"))
            extra = dim(f" (failed on run {case['iteration']}/{case['repeat']})") if case.get("iteration") else ""
            icon = yellow("–") if case["status"] == "skipped" else red("✗")
            out.append(f"    {icon} {case['name']}  {dim(label)}{extra}")
            if case.get("message"):
                prefix = f"step {case['step']}: " if "step" in case else ""
                out.append(f"        {prefix}{case['message']}")
            if "expected" in case:
                out.append(f"        expected: {json.dumps(case['expected'])}")
                out.append(f"        actual:   {json.dumps(case['actual'])}")
    p, t = totals(result)
    out.append("")
    out.append((green if p == t else red)(f"  {p}/{t} scenarios passed"))
    return "\n".join(out)
