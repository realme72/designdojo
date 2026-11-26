# Reposts

`repost(user, post_id)` shares someone's post: it shows up in the feeds of the reposter's
followers (and the reposter's own) at the moment of the repost. A feed never shows the same post
twice: if it arrives several ways, it appears once, at its newest position. Reposting the same
post twice returns `false` (no-op); reposting an unknown or deleted post raises `UnknownPost`.
Deleting the original removes it everywhere, reposts included.

*Interviewer's question:* is a timeline a list of posts, or a list of events?
