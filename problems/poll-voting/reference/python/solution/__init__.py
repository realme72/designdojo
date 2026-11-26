from contract import Clock, Polls

from .polls import PollService


def create(clock: Clock) -> Polls:
    return PollService(clock)
