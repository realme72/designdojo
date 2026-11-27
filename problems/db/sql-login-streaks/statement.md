# Login Streaks

> **Interview questions** (tab next to Problem): start there.

Schema given: `users(id, name)` and `logins(user_id, logged_at)` (several logins per day are
possible). Days are UTC days.

| Query | Returns |
|---|---|
| `longest_streak()` | rows `name`, `streak`: each user's longest run of consecutive days with at least one login (users who never logged in: 0); by streak desc, name |
| `daily_active(:from_day, :to_day)` | rows `day`, `users`: distinct users per day for every day in the range, zero days included |
| `active_n_days_in_row(:n)` | rows `name`: users with a streak of at least `:n` days; by name |
