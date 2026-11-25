from __future__ import annotations

import bisect

from contract import Direction, ElevatorStatus


class Elevator:
    """Owns its position, direction and stops; knows how to take one step (LOOK algorithm)."""

    def __init__(self, eid: int):
        self.id = eid
        self.floor = 1
        self.direction = Direction.IDLE
        self._stops: list[int] = []  # sorted, unique

    def add_stop(self, floor: int) -> None:
        if self.direction is Direction.IDLE and floor == self.floor:
            return  # served immediately
        i = bisect.bisect_left(self._stops, floor)
        if i == len(self._stops) or self._stops[i] != floor:
            self._stops.insert(i, floor)

    def is_on_the_way(self, floor: int, direction: Direction) -> bool:
        if self.direction is Direction.IDLE:
            return True
        if self.direction is not direction:
            return False
        return floor > self.floor if direction is Direction.UP else floor < self.floor

    def _ahead(self) -> bool:
        if self.direction is Direction.UP:
            return bool(self._stops) and self._stops[-1] > self.floor
        return bool(self._stops) and self._stops[0] < self.floor

    def step(self) -> None:
        if not self._stops:
            self.direction = Direction.IDLE
            return
        if self.direction is Direction.IDLE:
            nearest = min(self._stops, key=lambda s: (abs(s - self.floor), -s))
            if nearest == self.floor:
                self._stops.remove(nearest)
                return
            self.direction = Direction.UP if nearest > self.floor else Direction.DOWN
        self.floor += 1 if self.direction is Direction.UP else -1
        i = bisect.bisect_left(self._stops, self.floor)
        if i < len(self._stops) and self._stops[i] == self.floor:
            self._stops.pop(i)
        if not self._stops:
            self.direction = Direction.IDLE
        elif not self._ahead():
            self.direction = Direction.DOWN if self.direction is Direction.UP else Direction.UP

    def status(self) -> ElevatorStatus:
        return ElevatorStatus(self.id, self.floor, self.direction, list(self._stops))
