from contract import Clock, Scheduler

from .scheduler import HeapScheduler


def create(clock: Clock) -> Scheduler:
    return HeapScheduler(clock)
