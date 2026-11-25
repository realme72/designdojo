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
