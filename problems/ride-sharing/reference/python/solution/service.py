from __future__ import annotations

import itertools
import threading

from contract import (DriverStatus, DuplicateDriver, InvalidState, NoDriverAvailable, RideService, RiderBusy, Trip,
                      TripStatus, UnknownDriver, UnknownTrip, VehicleClass)

from .matching import MatchingStrategy
from .model import Driver, TripRecord
from .pricing import PricingStrategy

T = TripStatus
ACTIVE = {T.ASSIGNED, T.STARTED}
TRANSITIONS = {(T.ASSIGNED, T.STARTED), (T.STARTED, T.COMPLETED), (T.ASSIGNED, T.CANCELLED)}


class Dispatch(RideService):
    def __init__(self, matching: MatchingStrategy, pricing: PricingStrategy):
        self._matching = matching
        self._pricing = pricing
        self._drivers: dict[str, Driver] = {}
        self._trips: dict[str, TripRecord] = {}
        self._active_by_rider: dict[str, str] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def _driver(self, driver_id: str) -> Driver:
        d = self._drivers.get(driver_id)
        if d is None:
            raise UnknownDriver(driver_id)
        return d

    def _trip(self, trip_id: str) -> TripRecord:
        t = self._trips.get(trip_id)
        if t is None:
            raise UnknownTrip(trip_id)
        return t

    @staticmethod
    def _view(t: TripRecord) -> Trip:
        return Trip(t.id, t.rider, t.driver, t.vehicle, t.status, t.fare)

    def add_driver(self, driver_id: str, vehicle: VehicleClass, x: int, y: int) -> None:
        with self._lock:
            if driver_id in self._drivers:
                raise DuplicateDriver(driver_id)
            self._drivers[driver_id] = Driver(driver_id, vehicle, x, y)

    def update_location(self, driver_id: str, x: int, y: int) -> None:
        with self._lock:
            d = self._driver(driver_id)
            d.x, d.y = x, y

    def set_online(self, driver_id: str, online: bool) -> None:
        with self._lock:
            d = self._driver(driver_id)
            if d.status is DriverStatus.ON_TRIP:
                raise InvalidState("driver is on a trip")
            d.status = DriverStatus.AVAILABLE if online else DriverStatus.OFFLINE

    def request_ride(self, rider: str, vehicle: VehicleClass, x: int, y: int, dest_x: int, dest_y: int) -> Trip:
        with self._lock:  # pick + mark busy must be atomic
            if rider in self._active_by_rider:
                raise RiderBusy(rider)
            d = self._matching.pick(list(self._drivers.values()), vehicle, x, y)
            if d is None:
                raise NoDriverAvailable(vehicle.name)
            d.status = DriverStatus.ON_TRIP
            t = TripRecord(f"T{next(self._ids)}", rider, d.id, vehicle, (x, y), (dest_x, dest_y))
            self._trips[t.id] = t
            self._active_by_rider[rider] = t.id
            return self._view(t)

    def _move(self, trip_id: str, to: TripStatus) -> TripRecord:
        t = self._trip(trip_id)
        if (t.status, to) not in TRANSITIONS:
            raise InvalidState(f"{t.status.name} -> {to.name}")
        t.status = to
        if to not in ACTIVE:
            self._active_by_rider.pop(t.rider, None)
            self._drivers[t.driver].status = DriverStatus.AVAILABLE
        return t

    def start_trip(self, trip_id: str) -> Trip:
        with self._lock:
            return self._view(self._move(trip_id, T.STARTED))

    def end_trip(self, trip_id: str) -> Trip:
        with self._lock:
            t = self._move(trip_id, T.COMPLETED)
            t.fare = self._pricing.fare(t.vehicle, t.pickup, t.dest)
            d = self._drivers[t.driver]
            d.x, d.y = t.dest
            return self._view(t)

    def cancel_trip(self, trip_id: str) -> Trip:
        with self._lock:
            return self._view(self._move(trip_id, T.CANCELLED))

    def trip(self, trip_id: str) -> Trip:
        with self._lock:
            return self._view(self._trip(trip_id))

    def driver_status(self, driver_id: str) -> DriverStatus:
        with self._lock:
            return self._driver(driver_id).status
