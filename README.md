# Joinery

LLD practice playground. Pick a problem, implement it in Java or Python, and get judged
by hidden tests, concurrency races and (soon) a coach that points at your code.
See [SPEC.md](SPEC.md) for the full design.

## Setup

- Docker engine (OrbStack: `brew install --cask orbstack`, open it once)
- `uv sync`

## Web UI

```sh
(cd web && npm install && npm run build)   # once, and after frontend changes
uv run joinery serve --open                # http://127.0.0.1:8765
```

Problem statement, editor with file tree (autosave), Run (⌘↵) / Submit (⌘⇧↵),
results with compile errors shown in the editor, run history, and an interview timer.
Frontend dev with hot reload: `uv run joinery serve` + `cd web && npm run dev` (port 5174).

## Design coach

Reviews your design against the problem's decision points: line-anchored comments naming
the principle or pattern, why it matters in this problem, and three hints revealed one at
a time. Uses Groq's free tier:

```sh
cp .env.example .env        # then set GROQ_API_KEY
uv run joinery review work/parking-lot-java --hints 2
```

Each review is budgeted to ~5.2k input + 2k output tokens (under the 8k tokens/minute
limit) and cached by content, so re-reviewing an unchanged design is free. Models rotate
when one hits its daily limit (`JOINERY_COACH_MODELS` to change the order). Interview
mode keeps the coach locked until you Submit.

**When Groq isn't available** (no key, daily limit, network), reviews fall back to an
offline coach built from static analysis: each detected signal becomes a comment with the
principle, three hints and why it matters in this problem, matched to the problem's
decision points (via their `keywords`). It's clearly labelled, never invents a design score,
and marks decision points without signals "not assessed" rather than "good".

## CLI

```sh
uv run joinery list
uv run joinery scaffold parking-lot --lang java          # -> work/parking-lot-java/
# read work/parking-lot-java/PROBLEM.md, implement solution/
uv run joinery run    work/parking-lot-java              # visible sample scenarios
uv run joinery submit work/parking-lot-java              # + hidden + concurrency
```

Your workspace's `contract/` is generated (for your IDE). The judge regenerates it on
every run, so edits there have no effect. Code goes in `solution/`.

## Tests

```sh
uv run pytest            # Docker-backed tests skip if no engine is running
```

## Layout

```
problems/<id>/      problem package: statement, contract, scenarios, decision points, reference solutions
runners/<lang>/     in-container scenario runners + Dockerfiles (image tag = hash of this dir)
src/joinery/        CLI, contract parser, codegen, docker judge, report, server (FastAPI)
web/                React + Vite + Monaco frontend
tests/              unit + end-to-end (reference must pass; naive fixture must be caught)
```
