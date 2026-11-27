from __future__ import annotations

from abc import ABC, abstractmethod

from contract import Direction

from .elevator import Elevator


class DispatchStrategy(ABC):
    @abstractmethod
    def choose(self, elevators: list[Elevator], floor: int, direction: Direction) -> Elevator: ...


class NearestOnTheWay(DispatchStrategy):
    """Nearest elevator already heading that way (or idle); else nearest overall. Ties: lowest id."""

    def choose(self, elevators, floor, direction):
        on_way = [e for e in elevators if e.is_on_the_way(floor, direction)]
        pool = on_way or elevators
        return min(pool, key=lambda e: (abs(e.floor - floor), e.id))
