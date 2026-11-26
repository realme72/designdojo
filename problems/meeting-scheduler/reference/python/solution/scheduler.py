from __future__ import annotations

import bisect
import itertools
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from contract import (Booking, Clock, DuplicateRoom, InvalidCapacity, InvalidInterval, NoRoomAvailable, RoomScheduler,
                      Slot, UnknownBooking, UnknownRoom)


@dataclass
class Room:
    id: str
    capacity: int
    bookings: list[tuple[int, int, str]] = field(default_factory=list)  # sorted (start, end, booking id)

    def free(self, start: int, end: int) -> bool:
        i = bisect.bisect_left(self.bookings, (end,))
        return i == 0 or self.bookings[i - 1][1] <= start

    def gaps(self, start: int, end: int) -> list[Slot]:
        out, cursor = [], start
        for s, e, _ in self.bookings:
            if e <= cursor:
                continue
            if s >= end:
                break
            if s > cursor:
                out.append(Slot(cursor, s))
            cursor = max(cursor, e)
        if cursor < end:
            out.append(Slot(cursor, end))
        return out


class RoomPolicy(ABC):
    @abstractmethod
    def choose(self, candidates: list[Room]) -> Room: ...


class SmallestFit(RoomPolicy):
    def choose(self, candidates):
        return min(candidates, key=lambda r: (r.capacity, r.id))


class Scheduler(RoomScheduler):
    def __init__(self, clock: Clock, policy: RoomPolicy):
        self._clock = clock
        self._policy = policy
        self._rooms: dict[str, Room] = {}
        self._bookings: dict[str, Booking] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def add_room(self, room_id: str, capacity: int) -> None:
        if capacity < 1:
            raise InvalidCapacity(capacity)
        with self._lock:
            if room_id in self._rooms:
                raise DuplicateRoom(room_id)
            self._rooms[room_id] = Room(room_id, capacity)

    def book(self, organizer: str, attendees: int, start: int, end: int) -> Booking:
        if end <= start or start < self._clock.now():
            raise InvalidInterval(f"{start}..{end}")
        with self._lock:
            candidates = [r for r in self._rooms.values() if r.capacity >= attendees and r.free(start, end)]
            if not candidates:
                raise NoRoomAvailable(attendees)
            room = self._policy.choose(candidates)
            b = Booking(f"B{next(self._ids)}", room.id, organizer, start, end)
            bisect.insort(room.bookings, (start, end, b.id))
            self._bookings[b.id] = b
            return b

    def book_recurring(self, organizer: str, attendees: int, start: int, end: int, every_seconds: int,
                       count: int) -> list[Booking]:
        if end <= start or start < self._clock.now() or count < 1 or every_seconds < end - start:
            raise InvalidInterval(f"{start}..{end} every {every_seconds} x{count}")
        slots = [(start + k * every_seconds, end + k * every_seconds) for k in range(count)]
        with self._lock:
            candidates = [r for r in self._rooms.values()
                          if r.capacity >= attendees and all(r.free(s, e) for s, e in slots)]
            if not candidates:
                raise NoRoomAvailable(attendees)
            room = self._policy.choose(candidates)
            out = []
            for s, e in slots:
                b = Booking(f"B{next(self._ids)}", room.id, organizer, s, e)
                bisect.insort(room.bookings, (s, e, b.id))
                self._bookings[b.id] = b
                out.append(b)
            return out

    def cancel(self, booking_id: str) -> None:
        with self._lock:
            b = self._bookings.pop(booking_id, None)
            if b is None:
                raise UnknownBooking(booking_id)
            self._rooms[b.room].bookings.remove((b.start, b.end, b.id))

    def _room(self, room_id: str) -> Room:
        r = self._rooms.get(room_id)
        if r is None:
            raise UnknownRoom(room_id)
        return r

    def bookings(self, room_id: str) -> list[Booking]:
        with self._lock:
            return [self._bookings[bid] for _, _, bid in self._room(room_id).bookings]

    def free_slots(self, room_id: str, start: int, end: int) -> list[Slot]:
        with self._lock:
            room = self._room(room_id)
            if end <= start:
                raise InvalidInterval(f"{start}..{end}")
            return room.gaps(start, end)
