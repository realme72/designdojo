from contract import Airline, Clock

from .airline import AirlineSystem, LoadFactorFare, TwentyFourHourRefund


def create(clock: Clock) -> Airline:
    return AirlineSystem(clock, LoadFactorFare(), TwentyFourHourRefund())
