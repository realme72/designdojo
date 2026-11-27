# Ranked-choice polls

`create_ranked_poll(poll_id, options, closes_at)` creates a poll where each ballot **ranks**
one or more options (distinct, known options, else `InvalidChoice`). `results` shows
first-preference counts. `winners` (after closing) runs an instant runoff: while no option has
more than half of the ballots still in play, eliminate the option(s) with the fewest votes and
move those ballots to their next surviving preference (ballots with none left drop out). If
every remaining option is tied, they all win. Vote, retract and errors otherwise work as for
other polls.

*Interviewer's question:* was the counting rule a strategy already, or hard-wired into vote?
