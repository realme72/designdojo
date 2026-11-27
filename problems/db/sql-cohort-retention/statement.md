# Cohort Retention

> **Interview questions** (tab next to Problem): start there.

Schema given: `users(id, signed_up_at)` and `activity(user_id, active_on)` (one or more rows per
active day). A user's **cohort** is the UTC month they signed up. Month offset 0 is the signup
month, 1 the next calendar month, and so on.

| Query | Returns |
|---|---|
| `cohort_sizes()` | rows `cohort`, `users`: by cohort (first day of month) |
| `retention(:max_offset)` | rows `cohort`, `month_offset`, `retained`, `pct`: for every cohort and every offset 0..`:max_offset`, distinct users active in that month, and the percentage of the cohort (1 decimal); by cohort then offset |
| `returning_users(:month)` | a single value: users active in `:month` (first day given) who were also active in the previous month |
