# Sliding window counter

The sliding log uses too much memory at scale. Add a fourth algorithm,
`SLIDING_WINDOW_COUNTER`, which approximates a sliding window with two fixed-window counters.

- Windows are aligned to the epoch like `FIXED_WINDOW`. Let `prev` be the number of allowed
  requests in the previous window, `curr` in the current one, and `elapsed = now − start of
  the current window`.
- A request is allowed if `prev × (window − elapsed) / window + curr < limit`. To stay exact,
  compare integers: `prev × (window − elapsed) + curr × window < limit × window`.
- If the previous window isn't the one immediately before, `prev` is 0.

*Interviewer's question:* did adding an algorithm touch the limiter itself?
