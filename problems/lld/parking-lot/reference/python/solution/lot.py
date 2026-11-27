from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass

from contract import (AlreadyParked, Clock, InvalidTicket, LotFull, ParkingLotApi, Receipt, SpotSize, Ticket,
                      VehicleType)

from .allocation import Spot, SpotAllocator
from .pricing import DailyCapPricing


@dataclass(frozen=True)
class _Session:
    ticket: Ticket
    spot: Spot


class ParkingLot(ParkingLotApi):
    """Coordinates the gates: plate uniqueness, spot claim, ticket lifecycle.
    Policies (allocation, pricing, time) are injected, so this class doesn't change when they do."""

    def __init__(self, allocator: SpotAllocator, pricing: DailyCapPricing, clock: Clock):
        self._allocator = allocator
        self._pricing = pricing
        self._clock = clock
        self._lock = threading.Lock()          # guards _active and _plates together
        self._active: dict[str, _Session] = {}
        self._plates: set[str] = set()
        self._seq = itertools.count(1)

    def park(self, plate: str, vehicle_type: VehicleType) -> Ticket:
        with self._lock:
            if plate in self._plates:
                raise AlreadyParked(plate)
            self._plates.add(plate)            # reserve before the (separately locked) claim
        spot = self._allocator.claim(vehicle_type)
        if spot is None:
            with self._lock:
                self._plates.discard(plate)
            raise LotFull(f"no spot for {vehicle_type.name}")
        with self._lock:
            ticket = Ticket(f"T-{next(self._seq)}", plate, spot.floor, spot.size, spot.id, self._clock.now())
            self._active[ticket.id] = _Session(ticket, spot)
        return ticket

    def unpark(self, ticket_id: str) -> Receipt:
        with self._lock:
            session = self._active.pop(ticket_id, None)
            if session is None:
                raise InvalidTicket(ticket_id)
            self._plates.discard(session.ticket.plate)
        fee = self._pricing.fee_cents(session.spot.size, session.ticket.entry_time, self._clock.now())
        self._allocator.release(session.spot)
        return Receipt(ticket_id, fee)

    def available(self, size: SpotSize) -> int:
        return self._allocator.free(size)

    def set_daily_cap(self, size: SpotSize, cap_cents: int) -> None:
        self._pricing.set_cap(size, cap_cents)
