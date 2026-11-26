"""Composition root: the only place that knows which concrete policies are used."""

from contract import Clock, LotConfig, ParkingLotApi

from .allocation import Compatibility, SmallestFitAllocator, layout
from .lot import ParkingLot
from .pricing import HourlyPricing


def create(config: LotConfig, clock: Clock) -> ParkingLotApi:
    allocator = SmallestFitAllocator(layout(config.floors), Compatibility())
    pricing = HourlyPricing(config.hourly_rate_cents)
    return ParkingLot(allocator, pricing, clock)
