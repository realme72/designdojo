from contract import CarRental, Clock, RentalConfig

from .pricing import BaseFee, InsuranceFee, LateFee, MileageFee, Pricing
from .rental import RentalService


def create(config: RentalConfig, clock: Clock) -> CarRental:
    pricing = Pricing([BaseFee(), LateFee(config.late_multiplier),
                       MileageFee(config.free_km_per_day, config.per_km), InsuranceFee()])
    return RentalService(pricing, clock)
