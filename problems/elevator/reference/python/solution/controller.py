from __future__ import annotations

import threading

from contract import (Direction, ElevatorStatus, ElevatorSystem, InvalidFloor, InvalidRequest, NoElevatorAvailable,
                      UnknownElevator)

from .dispatch import DispatchStrategy
from .elevator import Elevator


class Controller(ElevatorSystem):
    def __init__(self, floors: int, count: int, dispatch: DispatchStrategy):
        self._floors = floors
        self._elevators = [Elevator(i) for i in range(1, count + 1)]
        self._dispatch = dispatch
        self._lock = threading.Lock()  # one short lock: dispatch reads every elevator's state

    def _check_floor(self, floor: int) -> None:
        if not 1 <= floor <= self._floors:
            raise InvalidFloor(floor)

    def _elevator(self, eid: int) -> Elevator:
        if not 1 <= eid <= len(self._elevators):
            raise UnknownElevator(eid)
        return self._elevators[eid - 1]

    def call(self, floor: int, direction: Direction) -> int:
        self._check_floor(floor)
        if direction is Direction.IDLE or (direction is Direction.UP and floor == self._floors) \
                or (direction is Direction.DOWN and floor == 1):
            raise InvalidRequest(f"{direction.name} from {floor}")
        with self._lock:
            usable = [e for e in self._elevators if e.in_service]
            if not usable:
                raise NoElevatorAvailable(floor)
            e = self._dispatch.choose(usable, floor, direction)
            e.add_stop(floor)
            return e.id

    def press(self, elevator_id: int, floor: int) -> None:
        e = self._elevator(elevator_id)
        self._check_floor(floor)
        with self._lock:
            if not e.in_service:
                raise InvalidRequest(f"elevator {elevator_id} is in maintenance")
            e.add_stop(floor)

    def set_maintenance(self, elevator_id: int, enabled: bool) -> None:
        e = self._elevator(elevator_id)
        with self._lock:
            e.set_maintenance(enabled)

    def step(self) -> None:
        with self._lock:
            for e in self._elevators:
                e.step()

    def status(self, elevator_id: int) -> ElevatorStatus:
        e = self._elevator(elevator_id)
        with self._lock:
            return e.status()
