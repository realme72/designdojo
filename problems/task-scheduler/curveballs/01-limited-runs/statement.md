# Limited repeats

`schedule_times(job_id, start_at, interval_seconds, times)`: a repeating job that runs at most
`times` times (same slots and catch-up behaviour as `schedule_every`), then disappears from
`pending`. `times < 1` or `interval_seconds < 1` raises `InvalidInterval`; other errors as for
`schedule_every`.

*Interviewer's question:* did you add a schedule, or teach the scheduler to count?
