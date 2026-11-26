from contract import Leaderboard

from .board import SortedBoard


def create() -> Leaderboard:
    return SortedBoard()
