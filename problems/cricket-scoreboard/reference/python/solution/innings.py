from __future__ import annotations

from dataclasses import dataclass

from contract import (BatterStats, BowlerChange, Extra, InningsOver, InvalidBall, SameBowler, Score, Scoreboard,
                      UnknownBatter)

from .rules import RULES

BALLS_PER_OVER = 6


@dataclass
class Batter:
    runs: int = 0
    balls: int = 0
    out: bool = False


class Innings(Scoreboard):
    def __init__(self, overs: int, order: list[str]):
        self._max_balls = overs * BALLS_PER_OVER
        self._order = order
        self._stats = {name: Batter() for name in order}
        self._striker, self._other = 0, 1
        self._next_in = 2
        self._runs = self._wickets = self._legal = 0
        self._over_bowler: str | None = None
        self._last_over_bowler: str | None = None

    def _complete(self) -> bool:
        return self._legal >= self._max_balls or self._wickets >= len(self._order) - 1

    def bowl(self, bowler: str, runs: int, extra: Extra, wicket: bool) -> Score:
        if self._complete():
            raise InningsOver()
        rule = RULES[extra]
        if not 0 <= runs <= 6 or (wicket and (not rule.legal or runs)):
            raise InvalidBall(f"{runs} {extra.name} wicket={wicket}")
        new_over = self._legal % BALLS_PER_OVER == 0 and self._over_bowler is None
        if new_over and bowler == self._last_over_bowler:
            raise SameBowler(bowler)
        if not new_over and bowler != self._over_bowler:
            raise BowlerChange(bowler)
        self._over_bowler = bowler

        striker = self._stats[self._order[self._striker]]
        self._runs += runs + rule.penalty
        if rule.runs_to_batter:
            striker.runs += runs
        if rule.faced:
            striker.balls += 1
        if wicket:
            striker.out = True
            self._wickets += 1
            if self._next_in < len(self._order):
                self._striker, self._next_in = self._next_in, self._next_in + 1
        elif runs % 2:
            self._swap()
        if rule.legal:
            self._legal += 1
            if self._legal % BALLS_PER_OVER == 0:  # over complete
                self._swap()
                self._last_over_bowler, self._over_bowler = bowler, None
        return self.score()

    def _swap(self) -> None:
        self._striker, self._other = self._other, self._striker

    def score(self) -> Score:
        return Score(self._runs, self._wickets, f"{self._legal // BALLS_PER_OVER}.{self._legal % BALLS_PER_OVER}",
                     self._complete())

    def striker(self) -> str:
        return "" if self._complete() else self._order[self._striker]

    def non_striker(self) -> str:
        return "" if self._complete() else self._order[self._other]

    def batter(self, name: str) -> BatterStats:
        b = self._stats.get(name)
        if b is None:
            raise UnknownBatter(name)
        return BatterStats(b.runs, b.balls, b.out)
