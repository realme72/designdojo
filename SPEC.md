# Joinery — v1 Spec

> *Joinery* is the craft of fitting pieces together so they hold under load.
> That's LLD: classes that compose cleanly, and tables that join cleanly.

A personal LLD practice playground. Pick a problem, design and implement it in
**Java or Python**, and get judged by hidden tests, change-request "curveballs",
and a **coach** that points at specific lines and says *"this is where
principle/pattern X would help, and here's why."*

Status: v1 (2026-11-26). **M0, M1, M2 (analyzer) and M5 (web UI) done**: Parking Lot
judged end-to-end in Java and Python from the CLI or browser, with design signals and a
class diagram. M3 (coach) and M4 (curveballs) next. Single user (self-prep). May go public later.

---

## 1. Scope

**In v1**
- Languages: Java 21, Python 3.12.
- 5 problems (§11), each with hidden tests, concurrency tests, 2–3 curveballs,
  decision points and a reference solution in both languages.
- Coach mode (hints on demand, layered) and Interview mode (timed, review at end).
- Line-anchored review: principles, patterns, smells, over-engineering.
- Auto-generated class diagram of *your* code.
- Runs locally. Docker sandbox. No auth.

**Not in v1** (design for it, don't build it)
- Auth, multi-user, payments, problem-authoring UI.
- More languages.
- DB design track (phase 2, §13).
- PrepRadar integration (later).

---

## 2. User flow

1. Pick a problem → read statement, requirements, the **public contract**.
2. Write code (web editor, or your own IDE via CLI).
3. `Run` → visible sample scenarios only.
4. `Review my design` (coach mode, anytime) → line comments + hints.
5. `Submit` → hidden tests + concurrency tests + structural analysis + coach review.
6. On pass, **Curveball 1 unlocks**: a new requirement. Modify your code, submit
   again. Joinery measures how much existing code you had to change.
7. Final report: scores, line comments, class diagram, curveball churn,
   comparison with the reference design's decision points.

---

## 3. Problem package format

Each problem is a directory. Everything is data. Adding a problem means writing
no harness code.

```
problems/parking-lot/
  problem.yaml            # metadata, statement, requirements
  contract.yaml           # language-neutral public API
  scenarios/
    sample.yaml           # visible
    hidden.yaml           # hidden
    concurrency.yaml      # hidden
  curveballs/
    01-ev-charging/
      statement.md
      contract.patch.yaml # API additions (if any)
      scenarios.yaml
    02-weekend-pricing/ ...
  decision_points.yaml    # where design choices matter + what good looks like
  rubric.yaml             # review criteria + weights
  reference/
    java/  python/        # reference solutions (never shown until finished)
```

### 3.1 problem.yaml
```yaml
id: parking-lot
title: Parking Lot
difficulty: medium
time_limit_min: 60          # interview mode
statement: statement.md
requirements:
  - Multiple floors, each with SMALL / MEDIUM / LARGE spots
  - Bikes fit SMALL+, cars MEDIUM+, trucks LARGE only
  - Issue a ticket on entry, compute fee on exit (hourly)
  - Must be safe under concurrent entry
```

### 3.2 contract.yaml
(Illustrative; the real one is `problems/parking-lot/contract.yaml`.)
The contract is the **only** thing the judge touches. Your internal model is
entirely your choice. Inputs and outputs are primitives, enums or small DTOs
defined by the contract, so the tests never depend on your class names.

```yaml
enums:
  VehicleType: [BIKE, CAR, TRUCK]
  SpotSize:    [SMALL, MEDIUM, LARGE]

dtos:
  Ticket:  { id: str, spot_id: str, entry_time: int }
  Receipt: { ticket_id: str, fee_cents: int }

provided:                   # harness-provided abstractions, injected
  Clock: { now: () -> int } # epoch seconds; tests control time

entrypoint:                 # how the judge builds your system
  create(config: LotConfig, clock: Clock) -> ParkingLotApi

interfaces:
  ParkingLotApi:
    park(plate: str, type: VehicleType) -> Ticket          # raises LotFull
    unpark(ticket_id: str) -> Receipt                      # raises InvalidTicket
    available(size: SpotSize) -> int

errors: [LotFull, InvalidTicket]
```

**Codegen**: `joinery scaffold parking-lot --lang java|python` produces:
- Java: `interface ParkingLotApi`, `record Ticket`, `enum VehicleType`,
  exceptions, `Clock` interface, plus an empty `Solution.create(...)`.
- Python: `Protocol`/ABC, `@dataclass(frozen=True)` DTOs, `Enum`s, exceptions,
  empty `create(...)`.

Injecting `Clock` is deliberate. It's DIP built into every problem, and it lets
tests fast-forward time.

---

## 4. Scenario DSL

Tests are written once as YAML and run by a small runner in each language.

```yaml
- name: car_cannot_use_small_spot
  config: { floors: [{ SMALL: 2, MEDIUM: 0, LARGE: 0 }] }
  steps:
    - call: park
      args: { plate: KA01, type: CAR }
      expect_error: LotFull

- name: hourly_fee_rounds_up
  config: { floors: [{ MEDIUM: 1 }], rates: { MEDIUM: 2000 } }
  steps:
    - call: park
      args: { plate: KA01, type: CAR }
      bind: t1                         # save result as $t1
    - advance_clock: 3700              # 1h 1m 40s
    - call: unpark
      args: { ticket_id: $t1.id }
      expect: { fee_cents: 4000 }
```

Step types: `call` (+ `args`, `expect` (subset match), `expect_error`, `bind`),
`advance_clock`, `parallel`, `assert`. References like `$t.id` or `$a[{i}].ok.id`
work in args and expectations; `{i}` is the thread index in `parallel`. A file-level
`config` is the default for every scenario in it. Every scenario gets a fresh system
and a judge clock starting at 1700000000.

### Concurrency
```yaml
- name: last_spot_race
  config: { floors: [{ MEDIUM: 10 }] }
  steps:
    - parallel:
        threads: 50
        call: park
        args: { plate: "P{i}", type: CAR }
        collect: results
    - assert: {of: results, ok_count: 10, error_count: {LotFull: 40}, unique: spot_id}
```
Other assertion: `assert: {distinct: [$a.id, $b.id]}`.

- **Java**: real threads spinning at a start line (not parked on a latch) so they
  hit the solution at the same instant; container gets 4 CPUs. Scenario `repeat: N`.
- **Python**: the GIL hides races (a naive unlocked solution passed every race
  scenario with plain threads). During `parallel` steps the runner sets
  `sys.setswitchinterval(1e-6)` and installs a **chaos scheduler**: a trace hook that
  yields the GIL between lines of solution code with p=0.3. With it, the naive
  fixture fails all 5 race scenarios in both languages, every run.
- Escape hatch (not built yet): hand-written `hidden_extra/` tests for cases the DSL
  can't express.

---

## 5. Sandbox / runner

One Docker container per run.

| | Java | Python |
|---|---|---|
| Image | `joinery-java:21` (Temurin + runner jar + Jackson) | `joinery-python:3.12` (runner + PyYAML) |
| Build | `javac` | none (`py_compile` for early syntax errors) |

Limits: `--network none`, `--read-only` + tmpfs `/work`, `--memory 512m`,
`--cpus 1` (4 for concurrency suites), `--pids-limit 256`, 20 s wall clock per suite,
non-root user.

Runner output (JSON on stdout):
```json
{ "suite": "hidden", "passed": 17, "failed": 1,
  "cases": [{ "name": "hourly_fee_rounds_up", "status": "fail",
              "step": 3, "expected": {"fee_cents": 4000},
              "actual": {"fee_cents": 2000}, "stderr": "" }] }
```
Hidden-test failure messages are shown by **case name only** (no expected
values), so you can't overfit to the tests. Sample tests show everything.

Prerequisite: Docker isn't installed yet → install **OrbStack** (or Colima).

---

## 6. Analyzer (deterministic)

**tree-sitter** (Java + Python grammars), run from the Python backend, so one
implementation covers both languages.

### 6.1 Class graph
Extracts classes, interfaces, enums, fields, methods, inheritance, implemented
interfaces, composition (field types), and dependencies (constructor and `new`
calls). Rendered as **Mermaid** `classDiagram` in the UI and also given to the coach.

### 6.2 Smell catalog → suggestions
Each detector outputs `{smell_id, file, line_start, line_end, evidence}`.

| ID | Detector | Usually suggests |
|---|---|---|
| `TYPE_SWITCH` | if/elif or switch on enum/type/`isinstance`/`instanceof` with ≥3 branches | Polymorphism / Strategy (OCP) |
| `STATE_FLAG` | Methods branching on a mutable status field that also gets reassigned | State pattern |
| `NEW_IN_LOGIC` | `new Concrete()` / `Concrete()` of a collaborator inside a business method | DIP / constructor injection / Factory |
| `GOD_CLASS` | >N methods, >M fields, or low cohesion (LCOM) | SRP split |
| `MANUAL_FANOUT` | Loop calling the same method on a listener list, plus hard-coded notifier types | Observer |
| `TELESCOPING_CTOR` | Constructor with ≥6 params, many optional/None | Builder / parameter object |
| `GLOBAL_STATE` | Static mutable field / module-level mutable singleton | Inject instead |
| `REFUSED_BEQUEST` | Override that throws UnsupportedOperation / NotImplementedError | LSP violation; rethink hierarchy |
| `FAT_INTERFACE` | Interface with many methods where implementers stub some out | ISP split |
| `PRIMITIVE_OBSESSION` | Money/time/ids passed around as raw int/str everywhere | Value objects |
| `UNGUARDED_SHARED` | Shared mutable collection mutated without a lock/atomic in concurrency problems | Synchronization / concurrent structures |
| `SPECULATIVE_PATTERN` | Factory with one product, interface with one trivial impl, Singleton without need | **Over-engineering**; simplify |

Detectors are allowed to be noisy. The coach decides what's worth reporting.

As built (M2): all of the above except `MANUAL_FANOUT` and `PRIMITIVE_OBSESSION`
(too noisy without type information), plus `DIRECT_TIME` (reads the system clock
instead of the injected Clock). Smells carry `level`: `warning` or `info` (a
single-implementation interface or a Singleton is `info`). `UNGUARDED_SHARED` only runs
for problems tagged `concurrency`, and treats `synchronized` methods/blocks,
`.lock()` callers and Python `with <lock>` blocks as guarded. Calibration: both
reference solutions produce zero warnings; the naive fixtures produce exactly
TYPE_SWITCH ×2 + UNGUARDED_SHARED.

---

## 7. Coach (LLM)

### 7.1 Inputs
- Problem statement, contract, current curveball (if any)
- Your code (all files, with line numbers)
- Class graph (§6.1)
- Smell hits (§6.2)
- `decision_points.yaml` and `rubric.yaml`
- Test results (case names and pass/fail)
- Mode + requested hint level

The reference solution is **not** sent, so the coach can't just steer you
toward copying it. Decision points describe *what good looks like*, not code.

### 7.2 decision_points.yaml
```yaml
- id: pricing
  question: How is the fee computed per spot/vehicle type?
  good: Pricing behind an abstraction (strategy/policy); adding a rate rule = new class.
  smells: [TYPE_SWITCH, PRIMITIVE_OBSESSION]
  principles: [OCP, SRP]
  patterns: [Strategy]
  curveball_link: 02-weekend-pricing
- id: allocation
  question: How is a spot chosen for a vehicle?
  good: Allocation strategy separate from lot bookkeeping.
  patterns: [Strategy]
  curveball_link: 03-nearest-to-gate
- id: concurrency
  question: What stops two cars getting the same spot?
  good: Atomic claim per spot or a lock scoped to allocation; no global lock on reads.
  smells: [UNGUARDED_SHARED]
```

### 7.3 Output (strict JSON, validated)
```json
{
  "summary": "Clean entity model; pricing and allocation are hard-coded.",
  "comments": [
    {
      "file": "ParkingLot.java", "line_start": 42, "line_end": 55,
      "kind": "suggestion",            // suggestion | praise | warning | overengineering
      "principle": "OCP",
      "pattern": "Strategy",
      "decision_point": "pricing",
      "title": "Fee calculation switches on vehicle type",
      "hints": [
        "What happens to this method when a new vehicle type or rate rule arrives?",
        "This violates Open/Closed. Consider isolating the varying part.",
        "Extract a PricingStrategy interface; one implementation per rule."
      ],
      "example": "interface PricingStrategy { long fee(Ticket t, long exitTs); } ...",
      "why_here": "Curveball 2 adds weekend pricing; this is exactly where it lands.",
      "confidence": 0.85
    }
  ],
  "decision_points": [
    { "id": "pricing", "status": "missed" },
    { "id": "concurrency", "status": "good" }
  ],
  "design_score": 58
}
```

### 7.4 Coaching rules (system prompt contract)
- Every comment is anchored to real lines. Evidence comes from code or a smell hit.
- Name the principle **and** explain why it matters *in this problem*. No textbook definitions.
- Praise good decisions explicitly.
- Recommend against patterns when they aren't justified (`overengineering`).
- Hints are layered: nudge → principle → concrete shape. The UI reveals them one at a time.
  `example` is only shown on request.
- Don't fail working code for style. Separate "wrong" from "could be better".
- Interview mode: no comments before submit.

### 7.5 Provider
Pluggable `CoachProvider` interface. **Open decision**: provider/model and budget.
Expect ~5–10k input tokens per review. Cache by `(code hash, curveball, hint level)`.

---

## 8. Curveballs & extensibility score

After the base suite passes, each curveball is a new requirement with its own
scenarios. The base scenarios must **also** keep passing (no regressions).

**Churn metric**: diff the class graph and AST before/after, at symbol level
(class, method):

- `added` = new classes/methods
- `modified` = existing methods whose body changed
- `deleted` = removed symbols

```
extensibility = added / (added + 2*modified + 2*deleted)    # 0..1
```

Report: *"Curveball 2: 1 class added, 3 existing methods modified
(ParkingLot.unpark, FeeCalculator.calc, Ticket.<init>)."* The coach links this
back to the relevant decision point (`curveball_link`).

---

## 9. Scoring (submit / interview mode)

| Component | Weight |
|---|---|
| Correctness (hidden scenarios) | 35 |
| Concurrency | 15 |
| Extensibility (curveballs: pass + churn) | 25 |
| Design review (coach `design_score`) | 25 |

Coach mode shows comments but no total score, because the point there is learning.

---

## 10. Architecture

```
web/  (React + Vite + Monaco, built to web/dist and served by FastAPI; no SSR needed locally)
  editor · run/submit · line comments in gutter · hint reveal · Mermaid diagram
        │  HTTP
src/joinery/  (Python 3.12, uv; FastAPI arrives with the web UI)
  problems loader · codegen · submissions · scoring
  ├─ runner/    docker SDK → per-run container, collects JSON
  ├─ analyzer/  tree-sitter → class graph, smells, churn diff
  └─ coach/     provider interface, prompt builder, JSON validation, cache
        │
Postgres 18 (local)  — submissions, results, reviews, curveball history
```

No queue in v1 (single user). Runs execute as background tasks.

CLI (built first; works with your own IDE):
```
joinery list
joinery scaffold parking-lot --lang java ./work/pl
joinery run      ./work/pl            # sample suite
joinery review   ./work/pl --hint 1   # coach mode
joinery submit   ./work/pl            # hidden + concurrency + review
joinery curveball ./work/pl --next
```

### Repo layout
```
joinery/
  SPEC.md
  problems/<id>/...
  runners/java/  runners/python/        # scenario runners + Dockerfiles
  src/joinery/  (codegen, judge, report, cli; later analyzer, coach, scoring, api)
  tests/        (unit + e2e; tests/fixtures/<problem>/<lang>/naive must be caught)
  web/
```

---

## 11. First 5 problems

| Problem | Decision points | Curveballs |
|---|---|---|
| **Parking Lot** | pricing, spot allocation, vehicle↔spot compatibility, last-spot race | EV charging spots (+fee); weekend/tiered pricing; nearest-to-gate allocation |
| **Elevator** | elevator state (State), dispatch strategy, request queue (Command), floor displays (Observer) | Maintenance mode; express elevator serving a subset of floors; swap dispatch algorithm |
| **Splitwise** | split types EQUAL/EXACT/PERCENT (Strategy + validation), expense model, balance ledger | SHARES split; multi-currency; simplify debts on settle-up |
| **BookMyShow** | seat hold & double-booking race, booking lifecycle (State), pricing, payment boundary (DIP) | Hold expiry after N min; occupancy-based dynamic pricing; stackable coupons (Decorator/Chain) |
| **Rate Limiter** | algorithm abstraction (Strategy), per-client config, Clock injection, concurrent counters | Per-endpoint tiers; add sliding-window-log algorithm; burst allowance |

Each problem ships with reference solutions in both languages that pass every
suite and curveball.

---

## 12. Milestones

| # | Deliverable | Done when |
|---|---|---|
| M0 | Install OrbStack; repo skeleton; uv project | `docker run hello-world` works |
| M1 | Contract codegen + scenario runners (Java & Python) + Parking Lot base suites + CLI `scaffold/run/submit` | Reference solutions pass, a broken solution fails, in both languages |
| M2 | Analyzer: class graph + smell catalog | Smells detected on deliberately smelly fixtures |
| M3 | Coach: provider, prompt, JSON schema, layered hints, `review` CLI | Useful line comments on the smelly fixture; none invented on the reference solution |
| M4 | Curveballs + churn metric + scoring | Strategy-based solution scores higher churn than switch-based on curveball 2 |
| M5 | Web UI: Monaco, gutter comments, hint reveal, Mermaid diagram, interview timer | Full flow in the browser |
| M6 | Remaining 4 problems | All reference solutions green |
| M7 | Phase 2: DB design track | §13 |

---

## 13. Phase 2: DB design track (sketch)

- Same problem, schema half: you write DDL (later, an ER editor that generates DDL).
- The problem lists **required queries** ("available MEDIUM spots on floor 2",
  "revenue per day"). You write them against *your* schema.
- Throwaway Postgres container: apply DDL → load seed generator data mapped to
  your schema → run your queries → compare result sets to expected.
- Checks: PK/FK/NOT NULL/UNIQUE constraints, normalization smells, `EXPLAIN`
  showing whether your indexes are actually used, and concurrency (`SELECT ... FOR UPDATE`
  vs unique constraints for seat booking).
- The coach reviews schema vs. queries ("this query needs 3 joins because ...").

Open question: seeding data into a user-defined schema. Likely approach: the
user writes a small mapping, or seeds go through their own INSERT statements.

---

## 14. Open decisions

1. LLM provider/model and monthly budget for the coach.
2. Java build: plain `javac` (v1) vs Gradle (if solutions need libs). Lean: plain `javac`, no deps.
3. Python typing: require type hints? Lean: optional, but the coach may suggest them.
