"""joinery command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import codegen, report
from .results import public_view
from .judge import JudgeError, Workspace, ensure_image, judge, scaffold
from .problems import SUITES, ProblemError, get_problem, list_problems


def cmd_list(_args) -> int:
    for p in list_problems():
        m = p.meta
        print(f"{p.id:<16} {m.get('difficulty', ''):<8} {p.title}")
    return 0


def cmd_scaffold(args) -> int:
    problem = get_problem(args.problem)
    dest = Path(args.dir or f"work/{problem.id}-{args.lang}")
    written = scaffold(problem, args.lang, dest)
    print(f"Workspace ready: {dest}")
    for p in written:
        print(f"  {p.relative_to(dest)}")
    entry = "solution/Solution.java" if args.lang == "java" else "solution/__init__.py"
    print(f"\nRead PROBLEM.md, start in {entry}, then: joinery run {dest}")
    return 0


def _judge(args, suites: list[str]) -> int:
    ws = Workspace.open(Path(args.dir))
    result = judge(ws, suites)
    if args.json:
        print(json.dumps(public_view(result), indent=2))
    else:
        print(report.render(result, ws.problem.title, ws.lang))
    passed, total = report.totals(result)
    return 0 if result.get("status") == "ok" and passed == total else 1


def cmd_run(args) -> int:
    return _judge(args, ["sample"])


def cmd_submit(args) -> int:
    return _judge(args, list(SUITES))


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
    print(f"Joinery on {url}")
    if args.open:
        import threading
        import webbrowser
        threading.Timer(1.0, webbrowser.open, [url]).start()
    uvicorn.run("joinery.server:app", host=args.host, port=args.port, reload=args.reload, log_level="warning")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="joinery", description="LLD practice playground")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list problems").set_defaults(fn=cmd_list)

    s = sub.add_parser("scaffold", help="create a workspace for a problem")
    s.add_argument("problem")
    s.add_argument("--lang", choices=codegen.LANGS, required=True)
    s.add_argument("dir", nargs="?", help="workspace dir (default: work/<problem>-<lang>)")
    s.set_defaults(fn=cmd_scaffold)

    for name, fn, help_ in (("run", cmd_run, "run the visible sample scenarios"),
                            ("submit", cmd_submit, "run sample + hidden + concurrency suites")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("dir", help="workspace dir")
        s.add_argument("--json", action="store_true", help="print raw result JSON")
        s.set_defaults(fn=fn)

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
    try:
        return args.fn(args)
    except (JudgeError, ProblemError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
