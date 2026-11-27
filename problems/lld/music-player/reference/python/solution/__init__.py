from contract import MusicPlayer

from .player import Player


def create() -> MusicPlayer:
    return Player()
