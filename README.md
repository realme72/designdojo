# DesignDojo

Design-interview practice in three **separate tracks**, each practised on its own:

| Track | Folder | What you practise |
|---|---|---|
| **Low-level design** | `problems/lld/` | In-memory object design, like the interview: entities, interfaces, SOLID, patterns, concurrency. Java or Python, judged by hidden tests and races. |
| **Database design** | `problems/db/` | Tables, keys, relationships and constraints on a real PostgreSQL 17, then the SQL (joins, CTEs, window functions). The database must reject bad data, and you can see how each query executes. |
| **High-level design** | `problems/hld/` | System design. Coming soon. |

The web UI opens on the track picker; each track has its own problem list, filters and
workspaces (`work/lld/…`, `work/db/…`). See [SPEC.md](SPEC.md) for the LLD design.

## Setup

- Docker engine (OrbStack: `brew install --cask orbstack`, open it once)
- `uv sync`

## Database design track

You get a domain (e.g. an online store) and design the schema in `solution/schema.sql`, plus one
small SQL file per operation or report in `solution/ops/` (`:param` placeholders). The judge
runs on PostgreSQL 17 in Docker (`postgres:17-alpine`, started on demand, data in memory):

- Every scenario gets a fresh copy of your schema inside a transaction that is rolled back, so
  tests are isolated; every operation runs in a savepoint, so it is atomic.
- Tests expect the **database** to refuse bad data: `expect_error: unique_violation`,
  `foreign_key_violation`, `check_violation`, `exclusion_violation`, or `rejected`
  (any constraint, data error or trigger RAISE).
- **Design review** reads the Postgres catalog: missing primary/foreign keys, unindexed foreign
  keys, money stored as float, free-text status columns, non-unique emails/SKUs, repeating
  column groups, `NOT IN (subquery)`, `SELECT *`, plus an **ER diagram**. The coach has a
  database-design rubric (normalization, keys, integrity, indexes, query quality, races).
- **Query flow**: after Run, every query in the sample scenarios is executed with
  `EXPLAIN ANALYZE` on that scenario's data and drawn as a flow (table scans → joins →
  grouping → sorting → result, real row counts on every arrow), next to the *logical* clause
  order (FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT) and plain-English
  insights. The **SQL console** runs anything against your schema, filled with a sample
  scenario's data, shows the rows and the same flow, and rolls everything back.

50 problems: 35 schema-design problems and 15 SQL query drills (schema given, you write the queries).
Every problem opens with **interview questions** ("relational or NoSQL, and why?") graded against a rubric.

**Social & content** (9)

| Problem | Difficulty | Focus |
|---|---|---|
| Notification Inbox | easy | idempotency-key, partial-index, preferences, batch-update |
| Forum with Votes (Reddit) | medium | upsert, composite-fk, recursive-cte, aggregation |
| Microblog (Twitter) | medium | m2m-tags, retweets, self-reference, regex |
| Music Streaming (Spotify) | medium | m2m, ordered-list, window-functions, time-series |
| Photo Sharing (Instagram) | medium | self-referencing-m2m, fan-out, aggregation, feed |
| Q&A Site (Stack Overflow) | medium | composite-fk, polymorphic-votes, tags, anti-join |
| Video Platform (YouTube) | medium | one-to-one, time-windows, top-n-per-group, counters |
| Chat Messaging (WhatsApp) | hard | composite-fk, idempotent-upsert, unread-counts, keyset-pagination |
| Professional Network (LinkedIn) | hard | symmetric-relationship, partial-unique-index, recursive-bfs, graph |

**Commerce & payments** (8)

| Problem | Difficulty | Focus |
|---|---|---|
| Coupon Engine | medium | usage-limits, counters, check-constraints, races |
| E-commerce Orders | medium | constraints, junction-table, aggregation, anti-join |
| Expense Sharing (Splitwise) | medium | composite-fk, exact-money-split, ordinality, aggregation |
| Multi-Warehouse Stock | medium | ledger, upsert, check-constraints, left-join-reports |
| Online Auctions | medium | conditional-update, races, check-constraints, reporting |
| Food Ordering (Swiggy) | hard | composite-fk, state-machine, partial-unique-index, price-snapshot |
| Subscription Billing | hard | exclusion-constraint, ranges, idempotent-billing, mrr |
| Wallet Ledger (Double-Entry) | hard | double-entry, idempotency, constraint-trigger, running-balance |

**Booking & reservations** (8)

| Problem | Difficulty | Focus |
|---|---|---|
| Library Loans | easy | partial-unique-index, trigger-limit, date-math, overdue |
| Restaurant Table Reservations | easy | exclusion-constraint, best-fit, time-ranges |
| Cinema Seat Booking (BookMyShow) | medium | generate-series, composite-fk, unique-per-show, exclusion |
| Clinic Appointments (Practo) | medium | exclusion-constraint, generate-series, gaps, partial-constraints |
| Parking Lot Sessions | medium | partial-unique-index, allocation, fees, lookup-table |
| Vehicle Rentals (Zoomcar) | medium | daterange, exclusion-constraint, range-intersection, pricing |
| Flight Reservations | hard | seat-allocation, self-join, intervals, check-constraints |
| Hotel Reservations | hard | exclusion-constraint, date-ranges, left-join, aggregation |

**Transport & logistics** (2)

| Problem | Difficulty | Focus |
|---|---|---|
| Parcel Tracking | medium | event-sourcing, state-machine, latest-per-group, time-math |
| Ride Hailing (Uber) | hard | partial-unique-index, nearest-neighbour, skip-locked, aggregation |

**SaaS & productivity** (8)

| Problem | Difficulty | Focus |
|---|---|---|
| Link Shortener Analytics (Bitly) | easy | generate-series, time-buckets, expiry, analytics |
| Online Courses (Udemy) | easy | composite-fk, ordered-children, progress, percentages |
| Calendar & Invites (Google Calendar) | medium | m2m-with-attributes, overlap-self-join, ranges, rsvp |
| Issue Tracker (Jira) | medium | per-parent-sequence, state-machine, audit-trigger, composite-fk |
| Org Chart & Salaries | medium | self-reference, recursive-cte, window-functions, cycle-prevention |
| Roles & Permissions (RBAC) | medium | m2m, role-hierarchy, recursive-cte, cycle-prevention |
| File Storage & Sharing (Google Drive) | hard | tree, nulls-not-distinct, inherited-permissions, recursive-cte |
| Multi-Tenant SaaS | hard | tenant-isolation, composite-fk, plan-limits, per-tenant-unique |

**SQL queries** (15)

| Problem | Difficulty | Focus |
|---|---|---|
| Duplicate Records Cleanup | easy | normalization, group-by-having, row-number, delete-using |
| Employee Salaries | easy | window-functions, dense-rank, nth-highest, correlated-subquery |
| Category Tree | medium | recursive-cte, paths, subtree-aggregation, depth |
| Conversion Funnel | medium | ordered-events, conditional-aggregation, self-join, percentages |
| Login Streaks | medium | gaps-and-islands, generate-series, date-math, window-functions |
| Median & Percentiles | medium | percentile-cont, ordered-set-aggregates, ntile |
| Mutual Friends & Recommendations | medium | symmetric-relationship, union-all, self-join, anti-join |
| Pivot & Subtotals | medium | conditional-aggregation, filter, rollup, grouping-sets |
| Running Balance & Statements | medium | running-sum, carry-forward, as-of-queries, first-occurrence |
| Sales Analytics | medium | lag, running-total, date-trunc, top-n-per-group |
| Top Rated with Ties | medium | having, distinct-on, rank, bayesian-average |
| Trip Cancellation Rate | medium | multiple-joins, filter-banned, conditional-aggregation, rounding |
| Cohort Retention | hard | cohorts, date-diff, conditional-aggregation, percentages |
| Sensor Time Series | hard | generate-series, rolling-window, gaps-and-islands, time-buckets |
| Sessionization | hard | lag, running-sum, gaps, window-functions |

```sh
uv run dojo list --track db
uv run dojo scaffold ecommerce-orders --lang sql      # -> work/db/ecommerce-orders-sql
uv run dojo run    work/db/ecommerce-orders-sql
uv run dojo submit work/db/ecommerce-orders-sql
```

## LLD problems (50)

Every problem ships with a statement, a language-neutral contract (Java + Python stubs are generated),
visible sample tests, hidden edge-case tests, concurrency race tests where relevant, decision points for
the coach, and a reference solution that passes every scenario (`uv run dojo validate`).

**Booking & reservations**

| Problem | Difficulty | Concurrency |
|---|---|---|
| Package Locker (Amazon Locker) | easy | yes |
| Airline Reservation System | medium | yes |
| Car Rental (Zoomcar) | medium | yes |
| Course Registration System | medium | yes |
| Doctor Appointment Booking (Practo) | medium | yes |
| Hotel Booking System | medium | yes |
| Library Management System | medium | yes |
| Movie Ticket Booking (BookMyShow) | medium | yes |
| Parking Lot | medium | yes |
| Ride Sharing (Uber / Ola) | hard | yes |

**Commerce & payments**

| Problem | Difficulty | Concurrency |
|---|---|---|
| ATM | medium |  |
| Digital Wallet (Paytm / PhonePe) | medium | yes |
| Inventory Management (Multi-warehouse) | medium | yes |
| Online Auction (eBay) | medium | yes |
| Shopping Cart & Promotions | medium |  |
| Splitwise | medium | yes |
| Food Delivery (Swiggy / Zomato) | hard | yes |
| Stock Exchange Order Matching | hard | yes |

**Data structures & caching**

| Problem | Difficulty | Concurrency |
|---|---|---|
| Game Leaderboard | easy | yes |
| LRU Cache | easy | yes |
| In-memory File System | medium |  |
| Key-Value Store with Transactions | medium |  |
| LFU Cache | medium | yes |
| Text Editor with Undo/Redo | medium |  |
| In-memory Database (mini SQL) | hard | yes |

**Games**

| Problem | Difficulty | Concurrency |
|---|---|---|
| Bowling Scorer | easy |  |
| Minesweeper | easy |  |
| Snake Game | easy |  |
| Snake and Ladder | easy |  |
| Tic-Tac-Toe (N×N) | easy |  |
| Cricket Scoreboard (Cricbuzz) | medium |  |
| Chess | hard |  |

**Infrastructure & control**

| Problem | Difficulty | Concurrency |
|---|---|---|
| Logging Framework | easy | yes |
| URL Shortener | easy | yes |
| Unique ID Generator (Snowflake) | easy | yes |
| Vending Machine | easy |  |
| Circuit Breaker | medium | yes |
| Elevator System | medium | yes |
| Load Balancer | medium | yes |
| Notification Service | medium | yes |
| Pub-Sub Message Broker | medium | yes |
| Rate Limiter | medium | yes |
| Traffic Signal Controller | medium |  |

**Scheduling & workflows**

| Problem | Difficulty | Concurrency |
|---|---|---|
| Meeting Room Scheduler | medium | yes |
| Task Scheduler (Cron-lite) | medium | yes |

**Social & content**

| Problem | Difficulty | Concurrency |
|---|---|---|
| Music Player (Spotify playlist) | easy |  |
| Polling & Voting System | easy | yes |
| Chat Application (WhatsApp) | medium | yes |
| News Feed (Twitter) | medium | yes |
| Q&A Site (Stack Overflow) | medium | yes |

## Curveballs (follow-up requirements)

Once every scenario passes, unlock the next curveball, the "now support X" follow-up an
interviewer asks next. Unlocking snapshots your code; each later submit measures how much
**existing** code the change forced you to edit (added/extended code is free, modified or
deleted code costs double, wiring in `create` is free), and folds it into the score:
correctness 35 · concurrency 15 · extensibility 25 · design 25 (components that don't apply
are left out and the rest re-weighted).

```sh
uv run dojo submit    work/lld/parking-lot-java   # score + churn report
uv run dojo curveball work/lld/parking-lot-java   # unlock the next one (needs all passing)
```

Every problem has at least one curveball (51 in total):

| Problem | Curveballs |
|---|---|
| Airline Reservation System | Premium economy |
| Package Locker (Amazon Locker) | Extra-large lockers |
| ATM | Mini statement |
| Bowling Scorer | Current frame |
| Car Rental (Zoomcar) | Insurance add-on |
| Chat Application (WhatsApp) | Delete for everyone |
| Chess | Undo |
| Circuit Breaker | Per-service settings |
| Course Registration System | Instructor override |
| Cricket Scoreboard (Cricbuzz) | Free hit |
| Digital Wallet (Paytm / PhonePe) | Transfer reversal |
| Doctor Appointment Booking (Practo) | Reschedule |
| Elevator System | Maintenance mode |
| In-memory File System | Copy |
| Food Delivery (Swiggy / Zomato) | Coupons |
| Hotel Booking System | Seasonal rates |
| Unique ID Generator (Snowflake) | Time-range queries |
| In-memory Database (mini SQL) | Unique constraints |
| Inventory Management (Multi-warehouse) | Warehouse priority |
| Key-Value Store with Transactions | Counters |
| Game Leaderboard | Dense ranking |
| LFU Cache | Pinned entries |
| Library Management System | Holds |
| Load Balancer | Sticky sessions |
| Logging Framework | JSON sink |
| LRU Cache | Resize at runtime |
| Meeting Room Scheduler | Recurring meetings |
| Minesweeper | Chording |
| Movie Ticket Booking (BookMyShow) | Row pricing |
| Music Player (Spotify playlist) | Repeat one |
| News Feed (Twitter) | Reposts |
| Notification Service | WhatsApp channel |
| Online Auction (eBay) | Reserve price |
| Parking Lot | Motorbikes; Daily price cap |
| Polling & Voting System | Ranked-choice polls |
| Pub-Sub Message Broker | Retention |
| Rate Limiter | Sliding window counter |
| Ride Sharing (Uber / Ola) | Surge pricing |
| Shopping Cart & Promotions | Bundle pricing |
| Snake and Ladder | Three sixes |
| Snake Game | Wrap-around mode |
| Splitwise | Split by shares |
| Q&A Site (Stack Overflow) | Bounties |
| Stock Exchange Order Matching | Immediate-or-cancel |
| Task Scheduler (Cron-lite) | Limited repeats |
| Text Editor with Undo/Redo | Replace all |
| Tic-Tac-Toe (N×N) | K in a row |
| Traffic Signal Controller | Uneven greens |
| URL Shortener | Click limits |
| Vending Machine | A new coin |

## Web UI

```sh
(cd web && npm install && npm run build)   # once, and after frontend changes
uv run dojo serve --open                # http://127.0.0.1:8765
```

Problem statement, editor with file tree (autosave), Run (⌘↵) / Submit (⌘⇧↵),
results with compile errors shown in the editor, run history, and an interview timer.
Frontend dev with hot reload: `uv run dojo serve` + `cd web && npm run dev` (port 5174).

## Design coach

Reviews your design against the problem's decision points: line-anchored comments naming
the principle or pattern, why it matters in this problem, and three hints revealed one at
a time. Uses Groq's free tier:

```sh
cp .env.example .env        # then set GROQ_API_KEY
uv run dojo review work/lld/parking-lot-java --hints 2
```

Each review is budgeted to ~5.2k input + 2k output tokens (under the 8k tokens/minute
limit) and cached by content, so re-reviewing an unchanged design is free. Models rotate
when one hits its daily limit (`DOJO_COACH_MODELS` to change the order). Interview
mode keeps the coach locked until you Submit.

**When Groq isn't available** (no key, daily limit, network), reviews fall back to an
offline coach built from static analysis: each detected signal becomes a comment with the
principle, three hints and why it matters in this problem, matched to the problem's
decision points (via their `keywords`). It's clearly labelled, never invents a design score,
and marks decision points without signals "not assessed" rather than "good".

## CLI

```sh
uv run dojo list
uv run dojo scaffold parking-lot --lang java          # -> work/lld/parking-lot-java/
# read work/lld/parking-lot-java/PROBLEM.md, implement solution/
uv run dojo run    work/lld/parking-lot-java              # visible sample scenarios
uv run dojo submit work/lld/parking-lot-java              # + hidden + concurrency
```

Your workspace's `contract/` is generated (for your IDE). The judge regenerates it on
every run, so edits there have no effect. Code goes in `solution/`.

## Tests

```sh
uv run pytest            # Docker-backed tests skip if no engine is running
uv run dojo validate  # authoring: lint every problem and run its reference solutions
```

## Layout

```
problems/<id>/      problem package: statement, contract, scenarios, decision points, reference solutions
runners/<lang>/     in-container scenario runners + Dockerfiles (image tag = hash of this dir)
src/designdojo/     CLI, contract parser, codegen, docker judge, report, server (FastAPI)
web/                React + Vite + Monaco frontend
tests/              unit + end-to-end (reference must pass; naive fixture must be caught)
```
