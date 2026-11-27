# Microblog (Twitter)

> **Interview questions** (tab next to Problem): start there.

Design the database for a microblogging service on **PostgreSQL 17**.

## Requirements

1. **Users** have a unique handle.
2. A **tweet** has an author, text of 1 to 280 characters and a time. A tweet may be a
   **reply** to another tweet.
3. Users **retweet** tweets, at most once each, never their own.
4. A tweet's **hashtags** (`#word`, case-insensitive, stored lower-case) are extracted when it is
   posted. The same tag twice in one tweet counts once.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:handle)` | one row: `id` |
| `post(:user_id, :body, :posted_at, :reply_to)` | one row: `id` (`:reply_to` is NULL for a new thread) |
| `retweet(:user_id, :tweet_id)` | nothing |
| `trending(:since, :n)` | rows `tag`, `tweets`: the `n` tags used by the most tweets posted at or after `:since`; ties by tag |
| `thread(:tweet_id)` | rows `id`, `depth`, `body`: the tweet and all replies below it, depth-first in posting order (depth 0 = the tweet) |
| `top_tweets(:n)` | rows `id`, `author`, `retweets`, `replies`: most retweeted first, then most replies, then id |

`regexp_matches(body, '#(\w+)', 'g')` finds hashtags; `WITH RECURSIVE` walks threads.
