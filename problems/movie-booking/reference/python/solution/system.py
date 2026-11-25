from __future__ import annotations

import itertools
import threading

from contract import (Booking, BookingSystem, Clock, DuplicateShow, HoldExpired, InvalidLayout, InvalidSeat,
                      SeatState, SeatUnavailable, UnknownBooking, UnknownHold, UnknownShow)

from .show import Hold, Show, seat_key


class Cinema(BookingSystem):
    def __init__(self, hold_seconds: int, clock: Clock):
        self._hold_seconds = hold_seconds
        self._clock = clock
        self._shows: dict[str, Show] = {}
        self._holds: dict[str, Hold] = {}
        self._bookings: dict[str, Booking] = {}
        self._registry = threading.Lock()  # guards the maps above; seat changes use the show's lock
        self._ids = itertools.count(1)

    def _show(self, show_id: str) -> Show:
        with self._registry:
            show = self._shows.get(show_id)
        if show is None:
            raise UnknownShow(show_id)
        return show

    def add_show(self, show_id: str, rows: int, cols: int) -> None:
        if not 1 <= rows <= 26 or cols < 1:
            raise InvalidLayout(f"{rows}x{cols}")
        with self._registry:
            if show_id in self._shows:
                raise DuplicateShow(show_id)
            self._shows[show_id] = Show(show_id, rows, cols)

    def hold(self, show_id: str, user: str, seats: list[str]) -> str:
        show = self._show(show_id)
        if not seats or len(set(seats)) != len(seats):
            raise InvalidSeat("empty or repeated seats")
        for s in seats:
            show.check(s)
        with show.lock:
            now = self._clock.now()
            if any(show.state(s, now) is not SeatState.AVAILABLE for s in seats):
                raise SeatUnavailable(show_id)
            hold = Hold(f"H{next(self._ids)}", show_id, user, tuple(seats), now + self._hold_seconds)
            for s in seats:
                show.held[s] = hold
        with self._registry:
            self._holds[hold.id] = hold
        return hold.id

    def _take_hold(self, hold_id: str, book: bool) -> Booking | None:
        """Atomically end an active hold, converting it to a booking in the same critical
        section, so its seats are never momentarily free for someone else to grab."""
        with self._registry:
            hold = self._holds.get(hold_id)
        if hold is None:
            raise UnknownHold(hold_id)
        show = self._show(hold.show_id)
        with show.lock:
            with self._registry:
                if self._holds.get(hold_id) is not hold:
                    raise UnknownHold(hold_id)
                if self._clock.now() >= hold.expires_at:
                    raise HoldExpired(hold_id)
                del self._holds[hold_id]
            for s in hold.seats:
                if show.held.get(s) is hold:
                    del show.held[s]
            if not book:
                return None
            booking = Booking(f"B{next(self._ids)}", hold.show_id, hold.user, sorted(hold.seats, key=seat_key))
            for s in hold.seats:
                show.booked[s] = booking.id
            with self._registry:
                self._bookings[booking.id] = booking
            return booking

    def confirm(self, hold_id: str) -> Booking:
        booking = self._take_hold(hold_id, book=True)
        assert booking is not None
        return booking

    def release(self, hold_id: str) -> None:
        self._take_hold(hold_id, book=False)

    def cancel(self, booking_id: str) -> None:
        with self._registry:
            booking = self._bookings.pop(booking_id, None)
        if booking is None:
            raise UnknownBooking(booking_id)
        show = self._show(booking.show_id)
        with show.lock:
            for s in booking.seats:
                show.booked.pop(s, None)

    def available(self, show_id: str) -> int:
        show = self._show(show_id)
        with show.lock:
            return show.free_count(self._clock.now())

    def seat_state(self, show_id: str, seat: str) -> SeatState:
        show = self._show(show_id)
        show.check(seat)
        with show.lock:
            return show.state(seat, self._clock.now())
