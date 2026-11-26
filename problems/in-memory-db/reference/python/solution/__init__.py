from contract import Database

from .db import MemoryDB


def create() -> Database:
    return MemoryDB()
