# Sessionization

> **Interview questions** (tab next to Problem): start there.

Schema given: `pageviews(id, user_id, url, viewed_at)`. A **session** is a run of a user's page
views where each view comes **at most 30 minutes** after the previous one; a longer gap starts a
new session. Sessions are numbered 1, 2, … per user in time order (ties: id).

| Query | Returns |
|---|---|
| `sessions()` | rows `user_id`, `session_no`, `started_at`, `ended_at`, `views`: by user, session |
| `avg_session_minutes()` | a single value: average of (ended − started) in minutes over all sessions, 1 decimal |
| `landing_pages()` | rows `url`, `sessions`: the first URL of each session, counted; by sessions desc, url |
