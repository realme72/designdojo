from __future__ import annotations

import heapq
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from contract import FloorConfig, SpotSize, VehicleType


@dataclass(frozen=True, order=True)
class Spot:
    """A physical spot. Ordered by (floor, index): the allocation order within one size."""
    floor: int
    index: int
    size: SpotSize = field(compare=False)
    id: str = field(compare=False)


def layout(floors: list[FloorConfig]) -> list[Spot]:
    spots = []
    for f, fc in enumerate(floors, start=1):
        for size, count in ((SpotSize.SMALL, fc.small), (SpotSize.MEDIUM, fc.medium), (SpotSize.LARGE, fc.large)):
            spots += [Spot(f, i, size, f"F{f}-{size.name[0]}{i}") for i in range(1, count + 1)]
    return spots


class Compatibility:
    """Which sizes each vehicle may use, smallest first. One table to edit for a new vehicle type."""

    _FITS = {
        VehicleType.BIKE: (SpotSize.SMALL, SpotSize.MEDIUM, SpotSize.LARGE),
        VehicleType.CAR: (SpotSize.MEDIUM, SpotSize.LARGE),
        VehicleType.TRUCK: (SpotSize.LARGE,),
    }

    def sizes_for(self, vehicle_type: VehicleType) -> tuple[SpotSize, ...]:
        try:
            return self._FITS[vehicle_type]
        except KeyError:
            raise ValueError(f"no compatibility rule for {vehicle_type}") from None


class SpotAllocator(ABC):
    """Owns spot occupancy. Implementations must be thread-safe."""

    @abstractmethod
    def claim(self, vehicle_type: VehicleType) -> Spot | None: ...

    @abstractmethod
    def release(self, spot: Spot) -> None: ...

    @abstractmethod
    def free(self, size: SpotSize) -> int: ...


class SmallestFitAllocator(SpotAllocator):
    """Smallest compatible size first, then lowest floor. One short critical section per call."""

    def __init__(self, spots: list[Spot], compatibility: Compatibility):
        self._compat = compatibility
        self._lock = threading.Lock()
        self._free: dict[SpotSize, list[Spot]] = {s: [] for s in SpotSize}
        for spot in spots:
            self._free[spot.size].append(spot)
        for heap in self._free.values():
            heapq.heapify(heap)

    def claim(self, vehicle_type: VehicleType) -> Spot | None:
        sizes = self._compat.sizes_for(vehicle_type)
        with self._lock:
            for size in sizes:
                if self._free[size]:
                    return heapq.heappop(self._free[size])
        return None

    def release(self, spot: Spot) -> None:
        with self._lock:
            heapq.heappush(self._free[spot.size], spot)

    def free(self, size: SpotSize) -> int:
        with self._lock:
            return len(self._free[size])
