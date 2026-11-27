# Circuit Breaker

Design a circuit breaker that protects calls to downstream services (one breaker per
service name, created on first use).

## Requirements

1. Config: `failure_threshold`, `open_seconds`, `trial_requests`.
2. **CLOSED** (initial): `allow_request` → `true`. `record_failure` counts *consecutive*
   failures (`record_success` resets the count). Reaching `failure_threshold` → **OPEN**.
3. **OPEN**: `allow_request` → `false` until `open_seconds` have passed since opening
   (`now ≥ opened_at + open_seconds`); then the breaker is **HALF_OPEN**.
   Results recorded while OPEN are ignored.
4. **HALF_OPEN**: `allow_request` grants at most `trial_requests` permits in total
   (further calls → `false`). Any `record_failure` → OPEN again (timer restarts).
   `trial_requests` successful results → CLOSED (counters reset).
5. `state(service)` reports `CLOSED`, `OPEN` or `HALF_OPEN`, taking elapsed time into account.
6. Many request threads share one breaker: permits and transitions must be race-free.

## Things an interviewer will push on

- Model the three states: who owns the transition rules?
- How do you avoid a thundering herd when the breaker half-opens?
- Failure-count vs failure-rate thresholds: how would you support both?
