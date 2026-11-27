from __future__ import annotations

from abc import ABC, abstractmethod

Board = list[list[str]]  # board[rank][file], rank 0 = rank 1; "." empty, upper = white
ORTHO = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIAG = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
KNIGHT = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]


def inside(r: int, f: int) -> bool:
    return 0 <= r < 8 and 0 <= f < 8


def is_white(p: str) -> bool:
    return p.isupper()


def enemy(p: str, q: str) -> bool:
    return q != "." and is_white(p) != is_white(q)


class Piece(ABC):
    @abstractmethod
    def targets(self, b: Board, r: int, f: int) -> list[tuple[int, int]]:
        """Pseudo-legal destinations (own-king safety is checked elsewhere, once)."""


class Stepper(Piece):
    def __init__(self, deltas):
        self.deltas = deltas

    def targets(self, b, r, f):
        p = b[r][f]
        out = []
        for dr, df in self.deltas:
            nr, nf = r + dr, f + df
            if inside(nr, nf) and (b[nr][nf] == "." or enemy(p, b[nr][nf])):
                out.append((nr, nf))
        return out


class Slider(Piece):
    def __init__(self, directions):
        self.directions = directions

    def targets(self, b, r, f):
        p = b[r][f]
        out = []
        for dr, df in self.directions:
            nr, nf = r + dr, f + df
            while inside(nr, nf):
                if b[nr][nf] == ".":
                    out.append((nr, nf))
                else:
                    if enemy(p, b[nr][nf]):
                        out.append((nr, nf))
                    break
                nr, nf = nr + dr, nf + df
        return out


class Pawn(Piece):
    def targets(self, b, r, f):
        p = b[r][f]
        step, start = (1, 1) if is_white(p) else (-1, 6)
        out = []
        if inside(r + step, f) and b[r + step][f] == ".":
            out.append((r + step, f))
            if r == start and b[r + 2 * step][f] == ".":
                out.append((r + 2 * step, f))
        for df in (-1, 1):
            nr, nf = r + step, f + df
            if inside(nr, nf) and enemy(p, b[nr][nf]):
                out.append((nr, nf))
        return out


PIECES: dict[str, Piece] = {
    "K": Stepper(ORTHO + DIAG), "N": Stepper(KNIGHT), "R": Slider(ORTHO),
    "B": Slider(DIAG), "Q": Slider(ORTHO + DIAG), "P": Pawn(),
}


def piece_for(p: str) -> Piece:
    return PIECES[p.upper()]
