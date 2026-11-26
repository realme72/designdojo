from contract import BowlingGame

from .game import Game


def create() -> BowlingGame:
    return Game()
