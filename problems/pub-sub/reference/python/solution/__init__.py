from contract import Broker

from .broker import InMemoryBroker


def create() -> Broker:
    return InMemoryBroker()
