from contract import Store

from .store import OnlineStore


def create() -> Store:
    return OnlineStore()
