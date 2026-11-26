# Daily price cap

Long stays are getting expensive, so management adds a **daily cap** per spot size.

- New: `set_daily_cap(size, cap_cents)` (`cap_cents < 1` → new error `InvalidCap`). A cap
  can be set or changed at any time; the cap in force **at unpark time** applies.
- With a cap, the billable hours (as before: rounded up, minimum 1) are split into full
  24-hour days plus a remainder. Each full day costs `min(24 × rate, cap)` and the
  remainder costs `min(remainder_hours × rate, cap)`.
- Sizes without a cap are charged exactly as before.

*Interviewer's question:* where did this rule land in your code, and what did you have to edit?
