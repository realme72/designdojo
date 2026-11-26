# Unique ID Generator (Snowflake)

Design a Snowflake-style generator of unique, roughly time-ordered 64-bit IDs for one worker.

## Requirements

1. Config: `epoch` (seconds), `worker_id` (0–1023, 10 bits), `sequence_bits`.
2. Layout: `id = (now − epoch) << (10 + sequence_bits) | worker_id << sequence_bits | sequence`.
3. `next_id()`: within the same second, `sequence` counts up from 0; it resets to 0 when
   the second changes. When the sequence space for the current second is used up →
   `SequenceExhausted` (a real system would wait for the next tick).
4. If the clock goes backwards compared to the last issued ID's second →
   `ClockMovedBackwards` (never issue a possibly duplicate ID).
5. `parse(id)` → `{timestamp, worker, sequence}` where `timestamp` is epoch seconds
   (i.e. `epoch` added back).
6. IDs must be strictly increasing for this worker and unique under heavy concurrency.

## Things an interviewer will push on

- Why does the layout give rough time ordering across workers?
- Clock skew: wait, error, or borrow from the future?
- How do workers get unique worker ids (coordination service)?
