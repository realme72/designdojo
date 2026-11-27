from __future__ import annotations

from abc import ABC, abstractmethod

from contract import DriverStatus, VehicleClass

from .model import Driver


class MatchingStrategy(ABC):
    @abstractmethod
    def pick(self, drivers: list[Driver], vehicle: VehicleClass, x: int, y: int) -> Driver | None: ...


class NearestDriver(MatchingStrategy):
    """Nearest available driver of the class within radius (squared distances: no floats)."""

    def __init__(self, max_radius: int):
        self.r2 = max_radius * max_radius

    def pick(self, drivers, vehicle, x, y):
        best = None
        for d in drivers:
            if d.vehicle is not vehicle or d.status is not DriverStatus.AVAILABLE:
                continue
            dist2 = (d.x - x) ** 2 + (d.y - y) ** 2
            if dist2 <= self.r2 and (best is None or (dist2, d.id) < best[0]):
                best = ((dist2, d.id), d)
        return best[1] if best else None
