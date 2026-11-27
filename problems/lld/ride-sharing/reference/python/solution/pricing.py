from __future__ import annotations

from abc import ABC, abstractmethod

from contract import VehicleClass


class PricingStrategy(ABC):
    @abstractmethod
    def fare(self, vehicle: VehicleClass, pickup: tuple[int, int], dest: tuple[int, int]) -> int: ...


class DistancePricing(PricingStrategy):
    def __init__(self, base: dict[VehicleClass, int], per_unit: dict[VehicleClass, int]):
        self.base, self.per_unit = dict(base), dict(per_unit)

    def fare(self, vehicle, pickup, dest):
        distance = abs(dest[0] - pickup[0]) + abs(dest[1] - pickup[1])
        return self.base[vehicle] + self.per_unit[vehicle] * distance
