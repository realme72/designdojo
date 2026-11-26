from contract import Clock, Hotel

from .hotel import HotelSystem
from .policies import NightlyPricing, TwoDayRefund


def create(clock: Clock) -> Hotel:
    return HotelSystem(clock, NightlyPricing(), TwoDayRefund())
