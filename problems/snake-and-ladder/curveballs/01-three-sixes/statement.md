# Three sixes

House rule: a six still earns another roll, but a **third six in a row** voids the whole
turn. The player goes back to where the turn started (ignoring the first two sixes) and the
turn passes to the next player. The `MoveResult` reports `from_pos` as the position before the
third roll and `to_pos` as the restored position.

*Interviewer's question:* where do turn rules live: game, player, or a rule object?
