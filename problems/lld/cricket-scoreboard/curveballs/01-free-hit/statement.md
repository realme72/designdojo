# Free hit

The delivery after a **no-ball** is a *free hit*: the batter cannot be dismissed, so a ball
with `wicket=true` on a free hit raises `InvalidBall`. If the free-hit delivery is itself a
wide or a no-ball, the free hit carries over to the next delivery. Add `is_free_hit()`: whether
the next delivery is a free hit.

*Interviewer's question:* is this a property of a delivery rule, or state of the innings?
