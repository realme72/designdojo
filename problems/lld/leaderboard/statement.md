# Game Leaderboard

Design a live leaderboard for an online game.

## Requirements

1. `add_score(player, points)` adds `points` (may be negative) to the player's total,
   creating the player at 0 first. Returns the new total.
2. Ordering: higher total first; equal totals ordered by player name (ascending).
3. **Rank** is standard competition ranking: equal totals share a rank and the next rank
   skips (`100, 90, 90, 80` → ranks `1, 2, 2, 4`).
4. `top(k)` returns the first `k` entries `{player, score, rank}` (`k < 1` → `InvalidArgument`).
5. `rank(player)` → the player's rank; `around(player, radius)` → the entries from
   `radius` positions above to `radius` positions below the player (clipped at the ends).
   Unknown player → `UnknownPlayer`.
6. `remove(player)` deletes a player (`UnknownPlayer` if absent).
7. Scores arrive concurrently from many game servers: no update may be lost.

## Things an interviewer will push on

- Which structure gives fast updates *and* fast rank queries (sorted set, skip list, BIT)?
- How would you shard a leaderboard with 100M players?
- Daily / weekly boards: how do you reset or window them?
