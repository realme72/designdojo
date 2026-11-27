# Video Platform (YouTube)

> **Interview questions** (tab next to Problem): start there.

Design the database for channels, videos, subscriptions and views (**PostgreSQL 17**).

## Requirements

1. **Users** have a unique email. A user owns **at most one channel**; channel handles are unique.
2. **Videos** belong to a channel: title, duration (seconds > 0), visibility `PUBLIC`,
   `UNLISTED` or `PRIVATE`, and an upload time.
3. Users **subscribe** to channels (once each, not to their own).
4. Every **view** is recorded with the viewer (or NULL for anonymous), the video and the time.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:email)` | one row: `id` |
| `create_channel(:user_id, :handle)` | one row: `id` |
| `upload(:channel_id, :title, :duration_s, :visibility, :uploaded_at)` | one row: `id` |
| `subscribe(:user_id, :channel_id)` | nothing |
| `view(:video_id, :user_id, :viewed_at)` | nothing |
| `trending(:since, :n)` | rows `title`, `channel`, `views`: public videos by views at or after `:since`; ties by title |
| `channel_stats(:channel_id)` | one row: `subscribers`, `videos` (public only), `total_views` (all its videos) |
| `subscriptions_feed(:user_id, :n)` | rows `title`, `channel`: newest public videos from subscribed channels, ties by title |
| `top_video_per_channel()` | rows `channel`, `title`, `views`: each channel's most viewed video (ties by title), channels by handle |
