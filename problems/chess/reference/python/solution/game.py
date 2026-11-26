from __future__ import annotations

import re

from contract import ChessGame, Color, GameOver, GameStatus, IllegalMove, InvalidSquare, MoveResult

from .pieces import Board, is_white, piece_for

STANDARD = ["rnbqkbnr", "pppppppp", "........", "........", "........", "........", "PPPPPPPP", "RNBQKBNR"]
SQUARE = re.compile(r"^[a-h][1-8]$")


def parse(sq: str) -> tuple[int, int]:
    if not SQUARE.match(sq):
        raise InvalidSquare(sq)
    return int(sq[1]) - 1, ord(sq[0]) - ord("a")


def name(r: int, f: int) -> str:
    return f"{chr(ord('a') + f)}{r + 1}"


class Game(ChessGame):
    def __init__(self, setup: list[str], to_move: Color):
        rows = setup or STANDARD
        self._b: Board = [list(row) for row in reversed(rows)]
        self._turn = to_move if setup else Color.WHITE
        self._status = self._compute_status()

    # ---- rules ----
    def _mine(self, p: str, color: Color) -> bool:
        return p != "." and is_white(p) == (color is Color.WHITE)

    def _attacked(self, b: Board, r: int, f: int, by_white: bool) -> bool:
        for rr in range(8):
            for ff in range(8):
                p = b[rr][ff]
                if p != "." and is_white(p) == by_white and (r, f) in piece_for(p).targets(b, rr, ff):
                    return True
        return False

    def _king_safe_after(self, fr, ff, tr, tf, color: Color) -> bool:
        b = [row[:] for row in self._b]
        b[tr][tf], b[fr][ff] = b[fr][ff], "."
        king = "K" if color is Color.WHITE else "k"
        kr, kf = next((r, f) for r in range(8) for f in range(8) if b[r][f] == king)
        return not self._attacked(b, kr, kf, by_white=color is not Color.WHITE)

    def _legal_targets(self, r: int, f: int, color: Color) -> list[tuple[int, int]]:
        p = self._b[r][f]
        if not self._mine(p, color):
            return []
        return [(tr, tf) for tr, tf in piece_for(p).targets(self._b, r, f) if self._king_safe_after(r, f, tr, tf, color)]

    def _in_check(self, color: Color) -> bool:
        king = "K" if color is Color.WHITE else "k"
        kr, kf = next((r, f) for r in range(8) for f in range(8) if self._b[r][f] == king)
        return self._attacked(self._b, kr, kf, by_white=color is not Color.WHITE)

    def _compute_status(self) -> GameStatus:
        has_move = any(self._legal_targets(r, f, self._turn) for r in range(8) for f in range(8))
        check = self._in_check(self._turn)
        if not has_move:
            return GameStatus.CHECKMATE if check else GameStatus.STALEMATE
        return GameStatus.CHECK if check else GameStatus.IN_PROGRESS

    # ---- API ----
    def move(self, from_sq: str, to_sq: str, promotion: str) -> MoveResult:
        fr, ff = parse(from_sq)
        tr, tf = parse(to_sq)
        if self._status in (GameStatus.CHECKMATE, GameStatus.STALEMATE):
            raise GameOver(self._status.name)
        if (tr, tf) not in self._legal_targets(fr, ff, self._turn):
            raise IllegalMove(f"{from_sq}-{to_sq}")
        piece = self._b[fr][ff]
        if piece.upper() == "P" and tr in (0, 7):
            choice = (promotion or "Q").upper()
            if choice not in ("Q", "R", "B", "N"):
                raise IllegalMove(f"cannot promote to {promotion!r}")
            piece = choice if is_white(piece) else choice.lower()
        captured = self._b[tr][tf]
        self._b[tr][tf], self._b[fr][ff] = piece, "."
        self._turn = Color.BLACK if self._turn is Color.WHITE else Color.WHITE
        self._status = self._compute_status()
        return MoveResult("" if captured == "." else captured, self._status)

    def turn(self) -> Color:
        return self._turn

    def status(self) -> GameStatus:
        return self._status

    def board(self) -> list[str]:
        return ["".join(row) for row in reversed(self._b)]

    def legal_moves(self, square: str) -> list[str]:
        r, f = parse(square)
        return sorted(name(tr, tf) for tr, tf in self._legal_targets(r, f, self._turn))
