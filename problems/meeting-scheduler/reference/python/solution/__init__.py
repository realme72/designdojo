from contract import Clock, RoomScheduler

from .scheduler import Scheduler, SmallestFit


def create(clock: Clock) -> RoomScheduler:
    return Scheduler(clock, SmallestFit())
