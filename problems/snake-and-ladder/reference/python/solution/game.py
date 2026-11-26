from __future__ import annotations

from contract import (DuplicatePlayer, Game, GameOver, GameStarted, InvalidRoll, MoveResult, NoPlayers, NotYourTurn,
                      UnknownPlayer)

from .board import Board

EXTRA_TURN_ROLL = 6


class SnakeLadderGame(Game):
    def __init__(self, board: Board):
        self._board = board
        self._order: list[str] = []
        self._pos: dict[str, int] = {}
        self._turn = 0
        self._started = False
        self._winner = ""

    def add_player(self, name: str) -> None:
        if self._started:
            raise GameStarted(name)
        if name in self._pos:
            raise DuplicatePlayer(name)
        self._order.append(name)
        self._pos[name] = 0

    def move(self, player: str, roll: int) -> MoveResult:
        if self._winner:
            raise GameOver(self._winner)
        if player not in self._pos:
            raise UnknownPlayer(player)
        if self._order[self._turn] != player:
            raise NotYourTurn(player)
        if not 1 <= roll <= 6:
            raise InvalidRoll(roll)
        self._started = True
        start = self._pos[player]
        end = self._board.destination(start, roll)
        self._pos[player] = end
        if end == self._board.size:
            self._winner = player
            return MoveResult(player, roll, start, end, True, "")
        if roll != EXTRA_TURN_ROLL:
            self._turn = (self._turn + 1) % len(self._order)
        return MoveResult(player, roll, start, end, False, self._order[self._turn])

    def position(self, player: str) -> int:
        if player not in self._pos:
            raise UnknownPlayer(player)
        return self._pos[player]

    def current_player(self) -> str:
        if self._winner:
            raise GameOver(self._winner)
        if not self._order:
            raise NoPlayers()
        return self._order[self._turn]

    def winner(self) -> str:
        return self._winner
