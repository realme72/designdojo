"""Builds the coach prompt inside a hard token budget.

Groq free tier allows 8k tokens/minute per model and reserves prompt + max_tokens, so a
review must fit in one request: ~5.2k input + 2k output. Code gets whatever the fixed
parts leave; when it doesn't fit, files without signals collapse to signature outlines.
"""

from __future__ import annotations

import re
from pathlib import Path

PROMPT_VERSION = "coach-v1"
INPUT_BUDGET = 5200
MAX_OUTPUT_TOKENS = 2000
MAX_COMMENTS = 8

SYSTEM = f"""You are DesignDojo's design coach for low-level-design (LLD) interview practice.
A candidate implemented the problem below. Review the DESIGN (OOP, SOLID, design patterns,
concurrency), not style. Teach: explain why something matters in THIS problem.

Rules:
- Anchor every comment to real line numbers from the CODE section. Never invent lines.
- STATIC SIGNALS come from a parser and can be false positives: confirm against the code first.
- Use DECISION POINTS as your rubric. Judge each one: good | partial | missed | not_applicable.
- Praise good decisions explicitly (kind "praise").
- Flag over-engineering (kind "overengineering"): patterns or abstractions with no reason to vary.
  An interface with one implementation is fine when a decision point says that axis will change.
- Separate correctness risks (kind "warning") from improvements (kind "suggestion").
- hints: exactly 3, progressively more revealing: (1) a question that nudges, (2) name the
  principle/pattern and why, (3) the concrete shape of the fix. Do not give full solutions.
- example: optional, <= 10 lines, only the essential shape.
- At most {MAX_COMMENTS} comments, most important first. Be concise.

Reply with ONE JSON object, no prose, exactly this shape:
{{"summary": "<= 3 sentences",
  "design_score": 0-100,
  "decision_points": [{{"id": "<id>", "status": "good|partial|missed|not_applicable", "note": "<= 1 sentence"}}],
  "comments": [{{"file": "solution/...", "line_start": N, "line_end": N,
                "kind": "suggestion|praise|warning|overengineering",
                "principle": "e.g. Open/Closed or null", "pattern": "e.g. Strategy or null",
                "decision_point": "<id or null>", "title": "<= 10 words",
                "hints": ["nudge", "principle", "shape"], "example": "code or null",
                "why_here": "<= 2 sentences tied to this problem", "confidence": 0.0-1.0}}]}}"""


SQL_SYSTEM = f"""You are DesignDojo's database design coach for interview practice (PostgreSQL).
A candidate designed a schema and wrote SQL operations/queries for the problem below. Review the
DESIGN: entities and relationships (1:1, 1:N, M:N via junction tables), keys (surrogate vs natural),
normalization (1NF-3NF, and when denormalizing is justified), integrity enforced BY THE DATABASE
(NOT NULL, UNIQUE, FOREIGN KEY with sensible ON DELETE, CHECK, EXCLUDE), data types (numeric for
money, timestamptz), indexes that match the access paths, and query quality (correct joins,
NULL-safety, CTEs/window functions where they clarify, no N+1 or accidental cross joins,
race conditions such as check-then-insert that need a constraint or locking). Teach: explain why
something matters in THIS problem.

Rules:
- Anchor every comment to real line numbers from the CODE section. Never invent lines.
- STATIC SIGNALS come from the Postgres catalog and simple checks; confirm against the code first.
- Use DECISION POINTS as your rubric. Judge each one: good | partial | missed | not_applicable.
- Praise good decisions explicitly (kind "praise").
- Flag over-engineering (kind "overengineering"): tables, indirection or denormalization with no
  requirement behind them.
- Separate correctness/integrity risks (kind "warning") from improvements (kind "suggestion").
- hints: exactly 3, progressively more revealing: (1) a question that nudges, (2) name the
  principle (e.g. "Referential integrity", "2NF", "Covering index") and why, (3) the concrete shape
  of the fix. Do not give full solutions.
- example: optional, <= 10 lines of SQL, only the essential shape.
- At most {MAX_COMMENTS} comments, most important first. Be concise.
- "principle" holds the database principle; "pattern" may name a modelling pattern
  (junction table, soft delete, ledger, adjacency list, closure table...) or null.

Reply with ONE JSON object, no prose, exactly this shape:
{{"summary": "<= 3 sentences",
  "design_score": 0-100,
  "decision_points": [{{"id": "<id>", "status": "good|partial|missed|not_applicable", "note": "<= 1 sentence"}}],
  "comments": [{{"file": "solution/...", "line_start": N, "line_end": N,
                "kind": "suggestion|praise|warning|overengineering",
                "principle": "e.g. Referential integrity or null", "pattern": "e.g. Junction table or null",
                "decision_point": "<id or null>", "title": "<= 10 words",
                "hints": ["nudge", "principle", "shape"], "example": "SQL or null",
                "why_here": "<= 2 sentences tied to this problem", "confidence": 0.0-1.0}}]}}"""


def system_for(lang: str) -> str:
    return SQL_SYSTEM if lang == "sql" else SYSTEM


def est_tokens(s: str) -> int:
    """Conservative estimate for mixed code/English (~3 chars per token)."""
    return len(s) // 3 + 1


DECL = re.compile(r"^\s*(@|class\b|def\b|async def\b|interface\b|enum\b|record\b|"
                  r"(public|private|protected|static|final|abstract|synchronized|default)\b)")


def number(src: str) -> str:
    return "\n".join(f"{i}| {line}" for i, line in enumerate(src.splitlines(), 1))


def outline(src: str) -> str:
    """Keep declaration lines (with their real numbers); elide bodies."""
    out, skipped = [], 0
    for i, line in enumerate(src.splitlines(), 1):
        if DECL.match(line) or (line.strip() and not line.startswith((" ", "\t"))):
            if skipped:
                out.append(f"   ... {skipped} lines omitted")
                skipped = 0
            out.append(f"{i}| {line}")
        else:
            skipped += 1
    if skipped:
        out.append(f"   ... {skipped} lines omitted")
    return "\n".join(out)


def requirements(statement: str, limit: int = 2600) -> str:
    """The statement minus the headings and the boilerplate contract section (curveballs kept)."""
    curveballs = re.findall(r"## Curveball \d+.*?(?=\n---\n|\Z)", statement, flags=re.S)
    text = statement.split("## The contract")[0] + "".join("\n\n" + c for c in curveballs)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit]


def build(*, title: str, statement: str, decision_points: list[dict], analysis: dict,
          files: dict[str, str], tests: str, system: str = SYSTEM) -> tuple[str, dict]:
    """Return (user_prompt, meta). meta records which files were outlined."""
    dps = "\n".join(
        f"- {d['id']}: {d['question']} Good: {d['good']}"
        + (f" Patterns: {', '.join(d['patterns'])}." if d.get("patterns") else "")
        + (f" Watch for: {', '.join(d['smells'])}." if d.get("smells") else "")
        for d in decision_points
    ) or "- (none provided: judge general LLD quality)"
    signals = "\n".join(
        f"- [{s['level']}] {s['id']} {s['file']}:{s['line_start']}-{s['line_end']} {s['evidence']}"
        for s in analysis["smells"]
    ) or "- none"
    classes = "\n".join(
        f"- {c['name']} ({c['kind']}) {c['file']}:{c['line_start']}-{c['line_end']}"
        + (f" extends {', '.join(c['extends'])}" if c["extends"] else "")
        + (f" implements {', '.join(c['implements'])}" if c["implements"] else "")
        + f"; fields: {', '.join(f['name'] for f in c['fields']) or '-'}"
        + f"; methods: {', '.join(m['name'] for m in c['methods']) or '-'}"
        for c in analysis["classes"]
    ) or "- none"

    graph_title = "CLASS GRAPH"
    if analysis.get("graph_text") is not None:
        graph_title, classes = "SCHEMA (from the Postgres catalog)", analysis["graph_text"]
    head = (f"PROBLEM: {title}\nREQUIREMENTS:\n{requirements(statement)}\n\n"
            f"DECISION POINTS:\n{dps}\n\nTEST RESULTS: {tests}\n\n"
            f"STATIC SIGNALS (parser output; confirm before using):\n{signals}\n\n"
            f"{graph_title}:\n{classes}\n\nCODE (line-numbered):\n")

    budget = INPUT_BUDGET - est_tokens(system) - est_tokens(head)
    flagged = {s["file"] for s in analysis["smells"]}
    rendered = {p: number(src) for p, src in files.items()}
    outlined: list[str] = []
    # collapse the largest un-flagged files first, then flagged ones if still needed
    order = sorted(files, key=lambda p: (p in flagged, -len(files[p])))
    for p in order:
        if sum(est_tokens(t) for t in rendered.values()) <= budget:
            break
        rendered[p] = outline(files[p])
        outlined.append(p)
    truncated = False
    total = sum(est_tokens(t) for t in rendered.values())
    if total > budget:  # last resort: hard cut, keeping file order
        truncated = True
        keep = budget * 3
        for p in sorted(rendered):
            rendered[p] = rendered[p][: max(0, keep)]
            keep -= len(rendered[p])

    code = "\n\n".join(f"=== {p} ===\n{t}" for p, t in sorted(rendered.items()) if t)
    user = head + code
    return user, {"outlined": outlined, "truncated": truncated, "input_tokens_est": est_tokens(system + user)}


def read_solution(root: Path, ext: str) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): p.read_text() for p in sorted((root / "solution").rglob(f"*{ext}"))}
