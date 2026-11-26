from contract import BoardConfig, Minesweeper

from .game import Game


def create(config: BoardConfig) -> Minesweeper:
    return Game(config.rows, config.cols, {(r, c) for r, c in config.mines})
