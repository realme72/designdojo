# Rate Limiter

Design an in-process rate limiter that an API gateway calls once per request.
Each client is configured with an algorithm, a `limit` and a `window_seconds`.

## Requirements

1. `configure(client_id, algorithm, limit, window_seconds)` sets (or replaces) a client's
   rule. Replacing a rule resets that client's state. `limit < 1` or `window_seconds < 1`
   → `InvalidRule`.
2. `allow(client_id)` returns `true` if the request may proceed (and records it), else
   `false`. Unknown client → `UnknownClient`.
3. Algorithms:
   - `FIXED_WINDOW`: windows are aligned to the epoch: window = `floor(now / window_seconds)`.
     At most `limit` allowed requests per window.
   - `SLIDING_WINDOW_LOG`: allowed if fewer than `limit` *allowed* requests happened in
     `(now - window_seconds, now]`. Rejected requests are not recorded.
   - `TOKEN_BUCKET`: capacity `limit`, starts full, refills continuously at
     `limit / window_seconds` tokens per second (fractions accumulate, capped at capacity).
     A request takes one whole token.
4. Use the injected `Clock` (epoch seconds) for all time.
5. Requests arrive concurrently: a limit must never be exceeded under parallel calls.

## Things an interviewer will push on

- How do you add a fourth algorithm (e.g. sliding window counter)?
- What's the memory cost of the sliding log, and when would you switch?
- How would this work across several gateway instances?
