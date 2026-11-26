# Bounties

`offer_bounty(user, question_id, amount)` puts up reputation to attract answers: the amount
leaves the offerer's reputation immediately and goes to the author of the **next** accepted
answer (on top of the usual acceptance bonus). It stays with that author even if the asker later
accepts another answer. One bounty per question; not on closed questions (`QuestionClosed`)
or questions that already have an accepted answer; amount must be at least 1 and at most the
offerer's reputation. Other violations raise `Forbidden`.

*Interviewer's question:* is a bounty a reputation rule, or a new kind of event?
