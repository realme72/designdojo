from contract import GameConfig, SnakeGame

from .game import Game


def create(config: GameConfig) -> SnakeGame:
    return Game(config.rows, config.cols, [tuple(f) for f in config.food])
