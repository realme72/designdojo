"""dojo: the DesignDojo command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import codegen, report
from .results import public_view
from .judge import JudgeError, Workspace, ensure_image, judge, scaffold
from .problems import ProblemError, get_problem, list_problems, reference_meta


def cmd_list(args) -> int:
    from .problems import TRACKS

    for t in [args.track] if args.track else TRACKS:
        ps = list_problems(t)
        print(report.bold(f"{TRACKS[t]['title']} ({t}): {len(ps)} problem(s)") if hasattr(report, "bold")
              else f"{TRACKS[t]['title']} ({t}): {len(ps)} problem(s)")
        for p in ps:
            print(f"  {p.id:<24} {p.meta.get('difficulty', ''):<8} {p.title}")
    return 0


def cmd_scaffold(args) -> int:
    problem = get_problem(args.problem)
    dest = Path(args.dir or f"work/{problem.track}/{problem.id}-{args.lang}")
    written = scaffold(problem, args.lang, dest)
    print(f"Workspace ready: {dest}")
    for p in written:
        print(f"  {p.relative_to(dest)}")
    entry = "solution/Solution.java" if args.lang == "java" else "solution/__init__.py"
    print(f"\nRead PROBLEM.md, start in {entry}, then: dojo run {dest}")
    return 0


def _latest_design_score(ws: Workspace) -> int | None:
    from .coach import latest

    rev = latest(ws)
    if rev and rev.get("meta", {}).get("source") == "ai" and rev.get("review"):
        return rev["review"].get("design_score")
    return None


def _judge(args, full: bool) -> int:
    from .curveballs import evaluate

    ws = Workspace.open(Path(args.dir))
    result = judge(ws, ws.suites if full else ["sample"])
    view = evaluate(ws, result, _latest_design_score(ws)) if full else public_view(result)
    if args.json:
        print(json.dumps(view, indent=2))
    else:
        title = ws.problem.title + (f" · curveball {ws.level}/{len(ws.problem.curveballs)}" if ws.level else "")
        print(report.render(result, title, ws.lang))
        if full:
            print(report.render_extras(view, ws))
    passed, total = report.totals(result)
    return 0 if result.get("status") == "ok" and passed == total else 1


def cmd_run(args) -> int:
    return _judge(args, full=False)


def cmd_submit(args) -> int:
    return _judge(args, full=True)


def cmd_curveball(args) -> int:
    from .curveballs import CurveballLocked, unlock_next

    ws = Workspace.open(Path(args.dir))
    total = len(ws.problem.curveballs)
    if args.status:
        print(f"{ws.problem.title}: curveball {ws.level}/{total} unlocked")
        for i in range(1, ws.level + 1):
            print(f"  {i}. {ws.problem.curveball_info(i)['title']}")
        return 0
    try:
        info = unlock_next(ws)
    except CurveballLocked as e:
        print(f"curveball: {e}", file=sys.stderr)
        return 1
    print(report.bold(f"Curveball {info['index']}/{total}: {info['title']}\n"))
    print(info["statement"])
    print(report.dim(f"\nThe contract in {ws.root}/contract was updated; your code was snapshotted so"
                     " `dojo submit` can measure how much existing code this change forces you to edit."))
    return 0


def cmd_analyze(args) -> int:
    from .analyzer import analyze

    ws = Workspace.open(Path(args.dir))
    a = analyze(ws.root, ws.lang, concurrency=ws.problem.concurrency, contract_types=ws.problem.contract_types)
    if args.json:
        print(json.dumps(a, indent=2))
        return 0
    if args.mermaid:
        print(a["mermaid"])
        return 0
    st = a["stats"]
    print(report.bold(f"{ws.problem.title} · {ws.lang} · design signals"))
    print(report.dim(f"{st['files']} files, {st['lines']} lines, {st['classes']} classes, "
                     f"{st['abstractions']} abstractions, {st['methods']} methods\n"))
    if not a["smells"]:
        print(report.green("  No smells detected."))
    for s in a["smells"]:
        mark = report.yellow("!") if s["level"] == "warning" else report.dim("i")
        print(f"  {mark} {s['title']}  {report.dim(s['file'] + ':' + str(s['line_start']))}")
        print(f"      {s['evidence']}")
        print(report.dim(f"      → {', '.join(s['suggests'])}"))
    print(report.dim("\n  These are signals, not verdicts. The coach (M3) decides which ones matter here."))
    return 0


def cmd_review(args) -> int:
    from .coach import CoachError, CoachUnavailable, review

    ws = Workspace.open(Path(args.dir))
    hist = ws.root / ".dojo-history.jsonl"
    last = json.loads(hist.read_text().splitlines()[-1]) if hist.exists() and hist.read_text().strip() else None
    try:
        out = review(ws, last_run=last, force=args.force)
    except (CoachError, CoachUnavailable) as e:
        print(f"coach: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    r, m = out["review"], out["meta"]
    print(report.bold(f"{ws.problem.title} · {ws.lang} · design review")
          + report.dim(f"  ({m['model']}{', cached' if m['cached'] else ''})"))
    if r["design_score"] is not None:
        print(f"\n  Design score: {report.bold(str(r['design_score']))}/100")
    print(f"  {r['summary']}\n")
    marks = {"good": report.green("✓"), "partial": report.yellow("~"), "missed": report.red("✗")}
    for d in r["decision_points"]:
        print(f"  {marks.get(d['status'], report.dim('·'))} {d['id']:<16} {report.dim(d['note'] or d['status'])}")
    for c in r["comments"]:
        tag = " · ".join(x for x in (c["principle"], c["pattern"]) if x)
        print(f"\n  {report.bold(c['title'])}  {report.dim(c['file'] + ':' + str(c['line_start']))}"
              + (f"  [{tag}]" if tag else "") + report.dim(f"  {c['kind']}"))
        for i, h in enumerate(c["hints"][: args.hints], 1):
            print(f"    hint {i}: {h}")
        if c["why_here"]:
            print(report.dim(f"    why here: {c['why_here']}"))
    if m.get("dropped_comments"):
        print(report.dim(f"\n  ({m['dropped_comments']} comment(s) dropped: they pointed at lines that don't exist)"))
    return 0


def _check_stub_compiles(problem, lang: str) -> str | None:
    """No reference in this language: make sure the generated contract + stub compile/import."""
    import tempfile

    with tempfile.TemporaryDirectory(dir=Path.home() / ".cache") as tmp:
        ws_dir = Path(tmp) / "ws"
        scaffold(problem, lang, ws_dir, level=len(problem.curveballs))  # fullest contract must compile
        result = judge(Workspace.open(ws_dir), ["sample"])
    if result.get("status") == "compile_error":
        return "; ".join(f"{d['file']}:{d['line']} {d['message']}" for d in result["diagnostics"])[:400]
    if result.get("status") != "ok":
        return result.get("status", "?")
    return None


def cmd_validate(args) -> int:
    from .problems import lint_problem

    from .problems import duplicate_ids

    problems = [get_problem(p) for p in args.problems] if args.problems else list_problems(args.track)
    bad = 0
    for d in duplicate_ids():
        print(report.red(f"duplicate problem id: {d}"))
        bad += 1
    for p in problems:
        issues = lint_problem(p)
        line = f"{p.id:<24}"
        if issues:
            bad += 1
            print(report.red(f"{line} lint: {len(issues)} issue(s)"))
            for i in issues:
                print(f"    {i}")
            continue
        if args.lint_only:
            print(report.green(f"{line} lint ok"))
            continue
        parts = []
        for lang in p.langs:
            ref = p.root / "reference" / lang
            if not (ref / "solution").is_dir():
                problem_msg = _check_stub_compiles(p, lang)
                parts.append(report.red(f"{lang} stub: {problem_msg}") if problem_msg else report.dim(f"{lang} stub ok"))
                bad += bool(problem_msg)
                continue
            meta = ref / ".dojo.json"
            want = reference_meta(p, lang)
            if not meta.exists() or meta.read_text() != want:
                meta.write_text(want)
            result = judge(Workspace.open(ref), p.suites_at(len(p.curveballs)))
            passed, total = report.totals(result)
            ok = result.get("status") == "ok" and passed == total
            parts.append((report.green if ok else report.red)(f"{lang} {passed}/{total}"))
            if not ok:
                bad += 1
                if args.verbose or result.get("status") != "ok":
                    print(report.render(result, p.title, lang))
                else:
                    for s in result["suites"]:
                        for case in s["cases"]:
                            if case["status"] != "pass":
                                parts.append(f"\n    ✗ {s['name']}/{case['name']}: {case.get('message', '')} "
                                             f"{json.dumps(case.get('expected')) if 'expected' in case else ''} "
                                             f"{json.dumps(case.get('actual')) if 'actual' in case else ''}")
        print(f"{line} " + "  ".join(parts))
    print(f"\n{len(problems) - bad}/{len(problems)} problems valid")
    return 1 if bad else 0


def cmd_build_images(args) -> int:
    for lang in codegen.LANGS:
        tag = ensure_image(lang, force=args.force, quiet=False)
        print(f"{lang}: {tag}")
    return 0


def cmd_serve(args) -> int:
    import uvicorn

    from .server import WEB_DIST

    if not WEB_DIST.is_dir():
        print("note: web UI not built (cd web && npm install && npm run build); serving the API only")
    url = f"http://{args.host}:{args.port}"
    print(f"DesignDojo on {url}")
    if args.open:
        import threading
        import webbrowser
        threading.Timer(1.0, webbrowser.open, [url]).start()
    uvicorn.run("designdojo.server:app", host=args.host, port=args.port, reload=args.reload, log_level="warning")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dojo", description="LLD practice playground")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list", help="list problems by track")
    s.add_argument("--track", choices=["lld", "db", "hld"])
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("scaffold", help="create a workspace for a problem")
    s.add_argument("problem")
    s.add_argument("--lang", choices=[*codegen.LANGS, "sql"], required=True)
    s.add_argument("dir", nargs="?", help="workspace dir (default: work/<problem>-<lang>)")
    s.set_defaults(fn=cmd_scaffold)

    for name, fn, help_ in (("run", cmd_run, "run the visible sample scenarios"),
                            ("submit", cmd_submit, "run sample + hidden + concurrency suites")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("dir", help="workspace dir")
        s.add_argument("--json", action="store_true", help="print raw result JSON")
        s.set_defaults(fn=fn)

    s = sub.add_parser("analyze", help="class graph + design smells (static; nothing is executed)")
    s.add_argument("dir", help="workspace dir")
    s.add_argument("--json", action="store_true")
    s.add_argument("--mermaid", action="store_true", help="print the class diagram as Mermaid")
    s.set_defaults(fn=cmd_analyze)

    s = sub.add_parser("review", help="design review from the coach (LLM; uses GROQ_API_KEY)")
    s.add_argument("dir", help="workspace dir")
    s.add_argument("--hints", type=int, default=1, choices=(1, 2, 3), help="how many hints to reveal per comment")
    s.add_argument("--force", action="store_true", help="ignore the cache")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_review)

    s = sub.add_parser("validate", help="lint problems and run their reference solutions (authoring)")
    s.add_argument("problems", nargs="*")
    s.add_argument("--lint-only", action="store_true")
    s.add_argument("--track", choices=["lld", "db", "hld"])
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("curveball", help="unlock the next curveball (requires a fully passing submit)")
    s.add_argument("dir", help="workspace dir")
    s.add_argument("--status", action="store_true", help="show unlocked curveballs instead")
    s.set_defaults(fn=cmd_curveball)

    s = sub.add_parser("serve", help="start the web UI")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--open", action="store_true", help="open a browser tab")
    s.add_argument("--reload", action="store_true", help="auto-reload on code changes (dev)")
    s.set_defaults(fn=cmd_serve)

    s = sub.add_parser("build-images", help="(re)build the runner Docker images")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_build_images)

    args = ap.parse_args(argv)
    from .coach.provider import load_env
    from .problems import REPO_ROOT

    load_env(REPO_ROOT / ".env")
    try:
        return args.fn(args)
    except (JudgeError, ProblemError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
