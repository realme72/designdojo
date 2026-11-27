from __future__ import annotations

from collections import deque

from contract import GameOver, GameState, InvalidMove, Minesweeper

HIDDEN, FLAGGED, OPEN = 0, 1, 2


class Game(Minesweeper):
    def __init__(self, rows: int, cols: int, mines: set[tuple[int, int]]):
        self.rows, self.cols, self.mines = rows, cols, mines
        self.cells = [[HIDDEN] * cols for _ in range(rows)]
        self.counts = [[sum((r + dr, c + dc) in mines for dr, dc in self._deltas()) for c in range(cols)]
                       for r in range(rows)]
        self.safe_left = rows * cols - len(mines)
        self._state = GameState.PLAYING

    @staticmethod
    def _deltas():
        return [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]

    def _inside(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _check(self, r: int, c: int) -> None:
        if self._state is not GameState.PLAYING:
            raise GameOver(self._state.name)
        if not self._inside(r, c):
            raise InvalidMove(f"({r},{c})")

    def reveal(self, row: int, col: int) -> int:
        self._check(row, col)
        if self.cells[row][col] != HIDDEN:
            raise InvalidMove("cell is flagged or open")
        if (row, col) in self.mines:
            self._state = GameState.LOST
            return 0
        opened = self._flood(row, col)
        self.safe_left -= opened
        if self.safe_left == 0:
            self._state = GameState.WON
        return opened

    def _flood(self, row: int, col: int) -> int:
        opened, queue = 0, deque([(row, col)])
        self.cells[row][col] = OPEN
        while queue:  # iterative BFS: no recursion depth issues on big boards
            r, c = queue.popleft()
            opened += 1
            if self.counts[r][c] == 0:
                for dr, dc in self._deltas():
                    nr, nc = r + dr, c + dc
                    if self._inside(nr, nc) and self.cells[nr][nc] == HIDDEN:
                        self.cells[nr][nc] = OPEN
                        queue.append((nr, nc))
        return opened

    def chord(self, row: int, col: int) -> int:
        self._check(row, col)
        if self.cells[row][col] != OPEN:
            raise InvalidMove("chord needs an open cell")
        around = [(row + dr, col + dc) for dr, dc in self._deltas() if self._inside(row + dr, col + dc)]
        if sum(self.cells[r][c] == FLAGGED for r, c in around) != self.counts[row][col]:
            raise InvalidMove("flag count does not match")
        targets = [(r, c) for r, c in around if self.cells[r][c] == HIDDEN]
        if any(t in self.mines for t in targets):
            self._state = GameState.LOST
            return 0
        opened = sum(self._flood(r, c) for r, c in targets if self.cells[r][c] == HIDDEN)
        self.safe_left -= opened
        if self.safe_left == 0:
            self._state = GameState.WON
        return opened

    def toggle_flag(self, row: int, col: int) -> None:
        self._check(row, col)
        state = self.cells[row][col]
        if state == OPEN:
            raise InvalidMove("cell is open")
        self.cells[row][col] = FLAGGED if state == HIDDEN else HIDDEN

    def state(self) -> GameState:
        return self._state

    def view(self) -> list[str]:
        lost = self._state is GameState.LOST

        def ch(r: int, c: int) -> str:
            if lost and (r, c) in self.mines:
                return "*"
            return {HIDDEN: "#", FLAGGED: "F"}.get(self.cells[r][c]) or str(self.counts[r][c])

        return ["".join(ch(r, c) for c in range(self.cols)) for r in range(self.rows)]
