# Photo Sharing (Instagram)

> **Interview questions** (tab next to Problem): start there. Relational or NoSQL for a social
> app? How would a feed scale? Then design the schema.

Design the core database of a photo-sharing app on **PostgreSQL 17**. Invalid data must be
rejected by the database.

## Requirements

1. **Users** have a username, unique **ignoring case**.
2. Users **follow** other users. Nobody follows themselves; following someone twice is rejected.
3. Users create **posts** (a caption and the time it was posted).
4. Users **like** posts, at most once per post.
5. Users **comment** on posts; a comment can't be empty.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:username)` | one row: `id` |
| `follow(:follower_id, :followee_id)` / `unfollow(...)` | nothing |
| `create_post(:user_id, :caption, :posted_at)` | one row: `id` |
| `like(:user_id, :post_id)` | nothing |
| `comment(:user_id, :post_id, :body)` | one row: `id` |
| `feed(:user_id, :n)` | rows `post_id`, `author`, `caption`, `likes`, `comments`: the `n` newest posts by people the user follows (not their own); newest `posted_at` first, ties by `post_id` descending |
| `suggestions(:user_id)` | rows `username`, `mutuals`: people followed by people the user follows, excluding the user and anyone already followed; most mutuals first, then username |

Careful with `feed`: counting likes and comments in the same query is a classic trap.
