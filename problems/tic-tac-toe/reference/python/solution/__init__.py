from contract import GameConfig, TicTacToe

from .game import Game


def create(config: GameConfig) -> TicTacToe:
    return Game(config.size)
