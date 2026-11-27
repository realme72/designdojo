from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone

from contract import (Clock, DuplicateRoom, Hotel, InvalidDates, InvalidRate, InvalidState, NoAvailability,
                      Reservation, ReservationStatus, RoomType, UnknownReservation)

from .policies import PricingPolicy, RefundPolicy

S = ReservationStatus
TRANSITIONS = {  # (from, to) pairs that are legal
    (S.CONFIRMED, S.CANCELLED), (S.CONFIRMED, S.CHECKED_IN), (S.CHECKED_IN, S.CHECKED_OUT),
}


@dataclass
class Room:
    number: str
    type: RoomType
    rate: int
    stays: dict[str, tuple[date, date]] = field(default_factory=dict)  # reservation id -> [in, out)

    def free(self, start: date, end: date) -> bool:
        return all(end <= s or start >= e for s, e in self.stays.values())


def parse(d: str) -> date:
    try:
        return date.fromisoformat(d) if len(d) == 10 else _bad(d)
    except ValueError:
        _bad(d)


def _bad(d: str):
    raise InvalidDates(d)


class HotelSystem(Hotel):
    def __init__(self, clock: Clock, pricing: PricingPolicy, refunds: RefundPolicy):
        self._clock = clock
        self._pricing = pricing
        self._refunds = refunds
        self._rooms: dict[str, Room] = {}
        self._res: dict[str, Reservation] = {}
        self._seq = itertools.count(1)
        self._order: dict[str, int] = {}
        self._lock = threading.Lock()

    def _today(self) -> date:
        return datetime.fromtimestamp(self._clock.now(), timezone.utc).date()

    def _range(self, check_in: str, check_out: str) -> tuple[date, date]:
        start, end = parse(check_in), parse(check_out)
        if end <= start or start < self._today():
            raise InvalidDates(f"{check_in}..{check_out}")
        return start, end

    def add_room(self, number: str, type: RoomType, nightly_rate: int) -> None:
        if nightly_rate < 1:
            raise InvalidRate(nightly_rate)
        with self._lock:
            if number in self._rooms:
                raise DuplicateRoom(number)
            self._rooms[number] = Room(number, type, nightly_rate)

    def set_seasonal_rate(self, type: RoomType, start: str, end: str, percent: int) -> None:
        s, e = parse(start), parse(end)
        if e <= s:
            raise InvalidDates(f"{start}..{end}")
        with self._lock:
            self._pricing.add_season(type, s, e, percent)

    def _free_rooms(self, type: RoomType, start: date, end: date) -> list[Room]:
        return sorted((r for r in self._rooms.values() if r.type is type and r.free(start, end)),
                      key=lambda r: r.number)

    def search(self, type: RoomType, check_in: str, check_out: str) -> list[str]:
        start, end = self._range(check_in, check_out)
        with self._lock:
            return [r.number for r in self._free_rooms(type, start, end)]

    def book(self, guest: str, type: RoomType, check_in: str, check_out: str) -> Reservation:
        start, end = self._range(check_in, check_out)
        with self._lock:
            free = self._free_rooms(type, start, end)
            if not free:
                raise NoAvailability(type.name)
            room = free[0]
            n = next(self._seq)
            res = Reservation(f"R{n}", guest, room.number, check_in, check_out,
                              self._pricing.total(room.rate, start, end, room.type), S.CONFIRMED)
            room.stays[res.id] = (start, end)
            self._res[res.id] = res
            self._order[res.id] = n
            return res

    def _transition(self, rid: str, to: ReservationStatus) -> Reservation:
        res = self._res.get(rid)
        if res is None:
            raise UnknownReservation(rid)
        if (res.status, to) not in TRANSITIONS:
            raise InvalidState(f"{res.status.name} -> {to.name}")
        res = replace(res, status=to)
        self._res[rid] = res
        return res

    def cancel(self, reservation_id: str) -> int:
        with self._lock:
            res = self._transition(reservation_id, S.CANCELLED)
            del self._rooms[res.room].stays[res.id]
            return self._refunds.refund(res.total, self._today(), parse(res.check_in))

    def check_in(self, reservation_id: str) -> Reservation:
        with self._lock:
            res = self._res.get(reservation_id)
            if res is None:
                raise UnknownReservation(reservation_id)
            if res.status is S.CONFIRMED and parse(res.check_in) != self._today():
                raise InvalidState("not the check-in date")
            return self._transition(reservation_id, S.CHECKED_IN)

    def check_out(self, reservation_id: str) -> Reservation:
        with self._lock:
            return self._transition(reservation_id, S.CHECKED_OUT)

    def reservations(self, guest: str) -> list[Reservation]:
        with self._lock:
            mine = [r for r in self._res.values() if r.guest == guest]
            return sorted(mine, key=lambda r: (r.check_in, self._order[r.id]))
