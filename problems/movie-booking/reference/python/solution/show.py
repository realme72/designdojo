from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field

from contract import InvalidSeat, SeatState

SEAT = re.compile(r"^([A-Z])([1-9][0-9]*)$")


def seat_key(seat: str) -> tuple[str, int]:
    m = SEAT.match(seat)
    return (m.group(1), int(m.group(2))) if m else ("", 0)


@dataclass
class Hold:
    id: str
    show_id: str
    user: str
    seats: tuple[str, ...]
    expires_at: int
    total: int = 0


@dataclass
class Show:
    """Owns its seats. One lock per show: holds on different shows never contend."""
    id: str
    rows: int
    cols: int
    booked: dict[str, str] = field(default_factory=dict)   # seat -> booking id
    held: dict[str, Hold] = field(default_factory=dict)    # seat -> hold
    lock: threading.Lock = field(default_factory=threading.Lock)
    row_prices: dict[str, int] = field(default_factory=dict)

    def price(self, seats) -> int:
        return sum(self.row_prices.get(seat_key(s)[0], 0) for s in seats)

    def check(self, seat: str) -> None:
        row, num = seat_key(seat)
        if not row or ord(row) - ord("A") >= self.rows or not 1 <= num <= self.cols:
            raise InvalidSeat(seat)

    def state(self, seat: str, now: int) -> SeatState:
        if seat in self.booked:
            return SeatState.BOOKED
        h = self.held.get(seat)
        if h is not None and now < h.expires_at:
            return SeatState.HELD
        return SeatState.AVAILABLE

    def free_count(self, now: int) -> int:
        taken = len(self.booked) + sum(1 for h in self.held.values() if now < h.expires_at)
        return self.rows * self.cols - taken
