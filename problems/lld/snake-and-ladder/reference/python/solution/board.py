from __future__ import annotations


class Board:
    """Squares 1..size; snakes and ladders are the same thing: a jump from one square to another."""

    def __init__(self, size: int, jumps: dict[int, int]):
        self.size = size
        self._jumps = dict(jumps)

    def destination(self, position: int, roll: int) -> int:
        target = position + roll
        if target > self.size:
            return position
        return self._jumps.get(target, target)
