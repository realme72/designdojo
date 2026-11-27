from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from contract import Strategy


@dataclass
class Server:
    id: str
    weight: int
    healthy: bool = True
    active: int = 0
    score: int = 0  # smooth WRR running score


class PickStrategy(ABC):
    @abstractmethod
    def pick(self, healthy: list[Server]) -> Server:
        """healthy is non-empty and sorted by id."""


class RoundRobin(PickStrategy):
    def __init__(self):
        self.last: str | None = None

    def pick(self, healthy):
        chosen = next((s for s in healthy if self.last is None or s.id > self.last), healthy[0])
        self.last = chosen.id
        return chosen


class SmoothWeighted(PickStrategy):
    def __init__(self, servers):
        for s in servers:
            s.score = 0

    def pick(self, healthy):
        for s in healthy:
            s.score += s.weight
        chosen = min(healthy, key=lambda s: (-s.score, s.id))  # highest score, ties lowest id
        chosen.score -= sum(s.weight for s in healthy)
        return chosen


class LeastConnections(PickStrategy):
    def pick(self, healthy):
        return min(healthy, key=lambda s: (s.active, s.id))


def make(strategy: Strategy, servers) -> PickStrategy:
    if strategy is Strategy.ROUND_ROBIN:
        return RoundRobin()
    if strategy is Strategy.WEIGHTED_ROUND_ROBIN:
        return SmoothWeighted(servers)
    return LeastConnections()
