# Cricket Scoreboard (Cricbuzz)

Design live scoring for one innings, ball by ball.

## Requirements

1. Config: `overs` (the innings limit) and the batting order `batters` (the first two open:
   `batters[0]` on strike, `batters[1]` at the other end).
2. `bowl(bowler, runs, extra, wicket)` records one delivery and returns the score.
   `runs` are the runs physically run/hit off the delivery (0–6, else `InvalidBall`).
   - `NONE`: runs to the striker; the striker faces a ball; a legal delivery.
   - `WIDE`: team gets 1 + runs; nobody faces a ball; **not** a legal delivery.
   - `NO_BALL`: team gets 1 + runs; runs go to the striker, who faces a ball; not legal.
   - `BYE` / `LEG_BYE`: runs to the team only; the striker faces a ball; legal.
3. **Strike** changes on an odd `runs`, and again after the 6th legal ball of an over.
4. **Wickets** (`wicket: true`) are only allowed on legal deliveries with `runs = 0`
   (else `InvalidBall`). The striker is out and the next batter in the order takes strike.
5. An over is 6 legal deliveries. The same bowler can't bowl two overs in a row
   (`SameBowler` on the first ball of the next over), and an over can't change bowler
   midway (`BowlerChange`).
6. The innings is complete after `overs` overs or when only one batter is left not out;
   any further delivery → `InningsOver`.
7. `score()` → `{runs, wickets, overs, complete}` with `overs` written like `"3.2"`
   (completed overs . legal balls in the current over). `striker()` / `non_striker()`
   (empty once complete). `batter(name)` → `{runs, balls, out}` (`UnknownBatter` if not in the order).

## Things an interviewer will push on

- Where do the extras rules live, and how would you add penalty runs?
- Event sourcing: storing balls vs storing totals?
- How would commentary or a live feed subscribe to updates?
