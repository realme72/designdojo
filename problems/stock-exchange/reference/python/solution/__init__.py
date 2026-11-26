from contract import Exchange

from .engine import MatchingEngine


def create() -> Exchange:
    return MatchingEngine()
