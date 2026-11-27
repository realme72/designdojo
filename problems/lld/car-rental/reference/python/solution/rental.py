from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field

from contract import (Bill, CarRental, Category, Clock, DuplicateCar, InvalidDates, InvalidOdometer, InvalidState,
                      NoCarAvailable, Rental, RentalStatus, UnknownRental)

from .pricing import Pricing, Trip

S = RentalStatus
TRANSITIONS = {(S.RESERVED, S.ACTIVE), (S.RESERVED, S.CANCELLED), (S.ACTIVE, S.RETURNED)}
DAY = 86400


@dataclass
class Car:
    id: str
    branch: str
    category: Category
    rate: int
    odometer: int
    rentals: list["RentalRecord"] = field(default_factory=list)


@dataclass
class RentalRecord:
    id: str
    car: Car
    start: int
    end: int
    status: RentalStatus = S.RESERVED
    odometer_out: int = 0
    insurance_per_day: int = 0

    def blocks(self, start: int, end: int) -> bool:
        if self.status in (S.CANCELLED, S.RETURNED):
            return False
        if self.status is S.ACTIVE:  # out on the road: blocks every later day until it comes back
            return self.start < end
        return start < self.end and self.start < end


class RentalService(CarRental):
    def __init__(self, pricing: Pricing, clock: Clock):
        self._pricing, self._clock = pricing, clock
        self._cars: dict[str, Car] = {}
        self._rentals: dict[str, RentalRecord] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def _today(self) -> int:
        return self._clock.now() // DAY

    def _check_dates(self, start: int, end: int) -> None:
        if end <= start or start < self._today():
            raise InvalidDates(f"{start}..{end}")

    def _free(self, branch: str, category: Category, start: int, end: int) -> list[Car]:
        return sorted((c for c in self._cars.values()
                       if c.branch == branch and c.category is category and not any(r.blocks(start, end) for r in c.rentals)),
                      key=lambda c: c.id)

    def add_car(self, car_id: str, branch: str, category: Category, daily_rate: int, odometer: int) -> None:
        with self._lock:
            if car_id in self._cars:
                raise DuplicateCar(car_id)
            self._cars[car_id] = Car(car_id, branch, category, daily_rate, odometer)

    def available(self, branch: str, category: Category, pickup_day: int, return_day: int) -> list[str]:
        self._check_dates(pickup_day, return_day)
        with self._lock:
            return [c.id for c in self._free(branch, category, pickup_day, return_day)]

    def reserve(self, customer: str, branch: str, category: Category, pickup_day: int, return_day: int) -> Rental:
        self._check_dates(pickup_day, return_day)
        with self._lock:
            free = self._free(branch, category, pickup_day, return_day)
            if not free:
                raise NoCarAvailable(category.name)
            r = RentalRecord(f"R{next(self._ids)}", free[0], pickup_day, return_day)
            free[0].rentals.append(r)
            self._rentals[r.id] = r
            return self._view(r)

    @staticmethod
    def _view(r: RentalRecord) -> Rental:
        return Rental(r.id, r.car.id, r.status)

    def _move(self, rid: str, to: RentalStatus) -> RentalRecord:
        r = self._rentals.get(rid)
        if r is None:
            raise UnknownRental(rid)
        if (r.status, to) not in TRANSITIONS:
            raise InvalidState(f"{r.status.name} -> {to.name}")
        return r

    def pick_up(self, rental_id: str) -> Rental:
        with self._lock:
            r = self._move(rental_id, S.ACTIVE)
            if self._today() < r.start:
                raise InvalidState("too early")
            r.status, r.odometer_out = S.ACTIVE, r.car.odometer
            return self._view(r)

    def return_car(self, rental_id: str, odometer: int) -> Bill:
        with self._lock:
            r = self._move(rental_id, S.RETURNED)
            if odometer < r.odometer_out:
                raise InvalidOdometer(odometer)
            trip = Trip(r.car.rate, r.end - r.start, max(0, self._today() - r.end), odometer - r.odometer_out,
                        r.insurance_per_day)
            r.status, r.car.odometer = S.RETURNED, odometer
            return self._pricing.bill(trip)

    def add_insurance(self, rental_id: str, per_day: int) -> None:
        with self._lock:
            r = self._rentals.get(rental_id)
            if r is None:
                raise UnknownRental(rental_id)
            if r.status is not S.RESERVED:
                raise InvalidState(f"{r.status.name}: insurance is added before pick-up")
            r.insurance_per_day = per_day

    def cancel(self, rental_id: str) -> Rental:
        with self._lock:
            r = self._move(rental_id, S.CANCELLED)
            r.status = S.CANCELLED
            return self._view(r)
