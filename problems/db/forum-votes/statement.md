# Forum with Votes (Reddit)

> **Interview questions** (tab next to Problem): start there.

Design a Reddit-like forum on **PostgreSQL 17**.

## Requirements

1. **Users** (unique username) and **communities** (unique name).
2. A **post** belongs to one community and has an author, a title and a creation time.
3. Users **vote** on posts: `+1` or `-1`, one vote per user per post. Voting again **changes**
   the vote; users can also remove their vote. Any other value is rejected.
4. **Comments** belong to a post and may reply to another comment, which must be on the **same
   post**. Comments can't be empty.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:username)`, `add_community(:name)` | one row: `id` |
| `create_post(:community_id, :user_id, :title, :created_at)` | one row: `id` |
| `vote(:user_id, :post_id, :value)` | nothing (insert or change the vote) |
| `unvote(:user_id, :post_id)` | nothing |
| `comment(:post_id, :user_id, :parent_id, :body)` | one row: `id` (`:parent_id` NULL for a top-level comment) |
| `top_posts(:community_id, :n)` | rows `post_id`, `title`, `score`: highest score (sum of votes; 0 if none) first, then newest, then id |
| `comment_tree(:post_id)` | rows `id`, `depth`, `body`: depth-first, siblings oldest first (by id) |
| `karma(:user_id)` | a single value: total score of the user's posts (0 if none) |
