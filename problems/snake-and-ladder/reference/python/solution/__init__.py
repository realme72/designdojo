from contract import BoardConfig, Game

from .board import Board
from .game import SnakeLadderGame


def create(config: BoardConfig) -> Game:
    return SnakeLadderGame(Board(config.size, {**config.snakes, **config.ladders}))
