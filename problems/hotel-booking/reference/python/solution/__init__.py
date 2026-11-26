from contract import Clock, Hotel

from .hotel import HotelSystem
from .policies import SeasonalPricing, TwoDayRefund


def create(clock: Clock) -> Hotel:
    return HotelSystem(clock, SeasonalPricing(), TwoDayRefund())
