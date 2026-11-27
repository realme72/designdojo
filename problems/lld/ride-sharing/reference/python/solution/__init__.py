from contract import RideConfig, RideService

from .matching import NearestDriver
from .pricing import DistancePricing
from .service import Dispatch


def create(config: RideConfig) -> RideService:
    return Dispatch(NearestDriver(config.max_radius), DistancePricing(config.base_fare, config.per_unit))
