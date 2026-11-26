from contract import KeyValueStore

from .store import TransactionalStore


def create() -> KeyValueStore:
    return TransactionalStore()
