from contract import Clock, LockerConfig, LockerStation

from .station import SmallestFit, Station


def create(config: LockerConfig, clock: Clock) -> LockerStation:
    return Station(config.hold_seconds, clock, SmallestFit())
