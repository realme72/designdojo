# News Feed (Twitter)

Design the core of a Twitter-like feed.

## Requirements

1. `post(user, post_id)` publishes a post (repeated id → `DuplicatePost`). Posts are
   ordered by when they were published (later = newer), across all users.
2. `follow(follower, followee)` / `unfollow(follower, followee)`. Following yourself →
   `InvalidFollow`; following twice is a no-op; unfollowing someone you don't follow →
   `NotFollowing`.
3. `feed(user, limit)` → up to `limit` post ids from the user and everyone they follow,
   newest first (`limit < 1` → `InvalidArgument`). Deleted posts never appear.
4. `delete(user, post_id)`: only the author may delete (`NotAuthor`); unknown → `UnknownPost`.
5. `like(user, post_id)` → `true` if this is a new like, `false` if the user already liked
   it. `likes(post_id)` → count. Unknown or deleted post → `UnknownPost`.
6. Feeds should not require scanning every post in the system.
7. Likes and posts arrive concurrently: no like is lost or double-counted.

## Things an interviewer will push on

- Fan-out on write vs fan-out on read: when does each win (celebrities)?
- How do you merge followees' timelines efficiently (k-way merge with a heap)?
- Where would ranking (not just recency) plug in?
