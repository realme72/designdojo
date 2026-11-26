# Polling & Voting System

Design the backend for in-app polls.

## Requirements

1. `create_poll(poll_id, options, closes_at, multi_choice)`. Invalid → `InvalidPoll`: fewer
   than 2 options, a repeated option, or `closes_at ≤ now`. Repeated id → `DuplicatePoll`.
2. `vote(poll_id, user, choices)`: a poll is closed once `now ≥ closes_at` → `PollClosed`.
   Each user votes once per poll → `AlreadyVoted`. `InvalidChoice`: empty, an unknown option,
   an option repeated, or more than one choice on a single-choice poll.
3. `retract(poll_id, user)` removes the user's vote while the poll is open (no vote →
   `NotVoted`); the user may vote again.
4. `results(poll_id)` → `{option, votes}` for every option in creation order.
5. `winners(poll_id)` → the options with the most votes, in creation order (all of them if
   tied, including all-zero). While the poll is open → `PollOpen`.
6. Unknown poll → `UnknownPoll`. Thousands vote at once: no vote is lost or double-counted.

## Things an interviewer will push on

- Where do voting rules live (single vs multi choice, ranked choice)?
- How would you prevent ballot stuffing across devices?
- Real-time results for millions of voters: counters vs recount?
