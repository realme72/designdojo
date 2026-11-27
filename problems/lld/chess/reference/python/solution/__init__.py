from contract import ChessConfig, ChessGame

from .game import Game


def create(config: ChessConfig) -> ChessGame:
    return Game(list(config.setup), config.to_move)
