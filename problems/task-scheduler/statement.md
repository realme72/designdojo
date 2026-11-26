# Task Scheduler (Cron-lite)

Design an in-process job scheduler. Instead of real threads, the host calls `tick()`;
everything due at the clock's current time runs then.

## Requirements

1. `schedule_once(job_id, run_at)`: run once at `run_at` (epoch seconds). `run_at` before
   now → `InvalidTime`.
2. `schedule_every(job_id, start_at, interval_seconds)`: run at `start_at`, then every
   `interval_seconds`. `interval_seconds < 1` → `InvalidInterval`; `start_at` before now →
   `InvalidTime`. Repeated job id (among scheduled jobs) → `DuplicateJob`.
3. `tick()` runs every due job (`next_run ≤ now`) and returns their ids ordered by
   `next_run`, then id. A one-off job is then finished. A recurring job runs **once** even if
   it missed several intervals; its next run is the first `start_at + k × interval` strictly
   after now.
4. `cancel(job_id)` removes a job; returns whether it existed.
5. `pause(job_id)` stops a job from running; `resume(job_id)` re-enables it. A resumed
   recurring job's next run is the first slot ≥ now; a resumed one-off keeps its time
   (it runs on the next tick if overdue). Unknown → `UnknownJob`.
6. `pending()` lists active (not paused) jobs as `{id, next_run}` ordered by `next_run`, then id.
7. Several workers may call `tick()` at once: each due run happens exactly once.

## Things an interviewer will push on

- Which data structure finds the next due job quickly?
- How would you add retries, timeouts or job dependencies?
- What's your catch-up policy for missed runs, and how would you make it configurable?
