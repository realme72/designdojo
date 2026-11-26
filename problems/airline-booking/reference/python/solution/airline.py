from __future__ import annotations

import heapq
import itertools
import threading
from dataclasses import dataclass, field

from contract import (Airline, Booking, Clock, DuplicateFlight, FlightDeparted, InvalidRequest, InvalidState,
                      NotEnoughSeats, SeatClass, UnknownBooking, UnknownFlight)

PREFIX = {SeatClass.ECONOMY: "E", SeatClass.BUSINESS: "B", SeatClass.PREMIUM_ECONOMY: "P"}


class LoadFactorFare:
    """+10% per quarter of the cabin already sold."""

    def per_seat(self, base: int, sold: int, capacity: int) -> int:
        step = 4 * sold // capacity if capacity else 0
        return base * (10 + step) // 10


class TwentyFourHourRefund:
    def refund(self, total: int, now: int, departs_at: int) -> int:
        return total if departs_at - now >= 86400 else total // 2


@dataclass
class Cabin:
    prefix: str
    capacity: int
    base: int
    free: list[int] = field(default_factory=list)  # heap of seat numbers

    def __post_init__(self):
        self.free = list(range(1, self.capacity + 1))

    @property
    def sold(self) -> int:
        return self.capacity - len(self.free)


@dataclass
class Flight:
    id: str
    origin: str
    destination: str
    departs_at: int
    cabins: dict[SeatClass, Cabin]
    lock: threading.Lock = field(default_factory=threading.Lock)


class AirlineSystem(Airline):
    def __init__(self, clock: Clock, fares: LoadFactorFare, refunds: TwentyFourHourRefund):
        self._clock, self._fares, self._refunds = clock, fares, refunds
        self._flights: dict[str, Flight] = {}
        self._bookings: dict[str, tuple[Booking, SeatClass, bool]] = {}  # pnr -> (booking, class, active)
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def add_flight(self, flight_id, origin, destination, departs_at, seats, fares) -> None:
        with self._lock:
            if flight_id in self._flights:
                raise DuplicateFlight(flight_id)
            cabins = {c: Cabin(PREFIX[c], seats.get(c, 0), fares.get(c, 0)) for c in SeatClass}
            self._flights[flight_id] = Flight(flight_id, origin, destination, departs_at, cabins)

    def search(self, origin, destination, seat_class, count, start, end) -> list[str]:
        now = self._clock.now()
        with self._lock:
            flights = list(self._flights.values())
        hits = [f for f in flights
                if f.origin == origin and f.destination == destination and start <= f.departs_at < end
                and f.departs_at > now and len(f.cabins[seat_class].free) >= count]
        return [f.id for f in sorted(hits, key=lambda f: (f.departs_at, f.id))]

    def book(self, passenger, flight_id, seat_class, count) -> Booking:
        with self._lock:
            f = self._flights.get(flight_id)
        if f is None:
            raise UnknownFlight(flight_id)
        if count < 1:
            raise InvalidRequest(count)
        with f.lock:  # availability + seats + price atomically per flight
            if self._clock.now() >= f.departs_at:
                raise FlightDeparted(flight_id)
            cabin = f.cabins[seat_class]
            if len(cabin.free) < count:
                raise NotEnoughSeats(flight_id)
            price = self._fares.per_seat(cabin.base, cabin.sold, cabin.capacity)
            numbers = [heapq.heappop(cabin.free) for _ in range(count)]
            booking = Booking(f"P{next(self._ids)}", flight_id, [f"{cabin.prefix}{n}" for n in numbers], price * count)
        with self._lock:
            self._bookings[booking.pnr] = (booking, seat_class, True)
        return booking

    def cancel(self, pnr: str) -> int:
        with self._lock:
            found = self._bookings.get(pnr)
            if found is None:
                raise UnknownBooking(pnr)
            booking, seat_class, active = found
            f = self._flights[booking.flight_id]
            now = self._clock.now()
            if not active or now >= f.departs_at:
                raise InvalidState(pnr)
            self._bookings[pnr] = (booking, seat_class, False)
        with f.lock:
            for seat in booking.seats:
                heapq.heappush(f.cabins[seat_class].free, int(seat[1:]))
        return self._refunds.refund(booking.total, now, f.departs_at)
