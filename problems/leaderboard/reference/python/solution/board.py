from __future__ import annotations

import bisect
import threading

from contract import InvalidArgument, Leaderboard, Ranked, RankingMode, UnknownPlayer


class SortedBoard(Leaderboard):
    """Totals map + a sorted list of (-score, name). Competition ranks: 1 + count of higher scores."""

    def __init__(self):
        self._totals: dict[str, int] = {}
        self._order: list[tuple[int, str]] = []
        self._lock = threading.Lock()
        self._mode = RankingMode.COMPETITION

    def set_ranking_mode(self, mode: RankingMode) -> None:
        with self._lock:
            self._mode = mode

    def _rank_of_score(self, score: int) -> int:
        higher = bisect.bisect_left(self._order, (-score, ""))
        if self._mode is RankingMode.DENSE:
            return len({neg for neg, _ in self._order[:higher]}) + 1
        return higher + 1

    def _entry(self, i: int) -> Ranked:
        neg, name = self._order[i]
        return Ranked(name, -neg, self._rank_of_score(-neg))

    def add_score(self, player: str, points: int) -> int:
        with self._lock:
            old = self._totals.get(player)
            if old is not None:
                self._order.pop(bisect.bisect_left(self._order, (-old, player)))
            new = (old or 0) + points
            self._totals[player] = new
            bisect.insort(self._order, (-new, player))
            return new

    def top(self, k: int) -> list[Ranked]:
        if k < 1:
            raise InvalidArgument(k)
        with self._lock:
            return [self._entry(i) for i in range(min(k, len(self._order)))]

    def _index(self, player: str) -> int:
        if player not in self._totals:
            raise UnknownPlayer(player)
        return bisect.bisect_left(self._order, (-self._totals[player], player))

    def rank(self, player: str) -> int:
        with self._lock:
            self._index(player)
            return self._rank_of_score(self._totals[player])

    def around(self, player: str, radius: int) -> list[Ranked]:
        if radius < 0:
            raise InvalidArgument(radius)
        with self._lock:
            i = self._index(player)
            return [self._entry(j) for j in range(max(0, i - radius), min(len(self._order), i + radius + 1))]

    def remove(self, player: str) -> None:
        with self._lock:
            i = self._index(player)
            self._order.pop(i)
            del self._totals[player]
