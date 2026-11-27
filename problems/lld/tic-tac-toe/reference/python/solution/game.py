from __future__ import annotations

from contract import GameOver, GameState, InvalidMove, Mark, MoveOutcome, TicTacToe

WIN_STATE = {Mark.X: GameState.X_WON, Mark.O: GameState.O_WON}
PLAYERS = (Mark.X, Mark.O)


class _Lines:
    """Running totals per row/column/diagonal: +1 for X, -1 for O. |total| == n means a win."""

    def __init__(self, n: int):
        self.n = n
        self.rows = [0] * n
        self.cols = [0] * n
        self.diag = 0
        self.anti = 0

    def add(self, row: int, col: int, delta: int) -> bool:
        self.rows[row] += delta
        self.cols[col] += delta
        if row == col:
            self.diag += delta
        if row + col == self.n - 1:
            self.anti += delta
        return self.n in (abs(self.rows[row]), abs(self.cols[col]), abs(self.diag), abs(self.anti))


class _Scan:
    """k-in-a-row check around the last move: walk both ways along each of 4 directions."""

    def __init__(self, cells, k: int):
        self.cells, self.k = cells, k

    def add(self, row: int, col: int, mark) -> bool:
        n = len(self.cells)
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            run = 1
            for sign in (1, -1):
                r, c = row + sign * dr, col + sign * dc
                while 0 <= r < n and 0 <= c < n and self.cells[r][c] is mark:
                    run += 1
                    r, c = r + sign * dr, c + sign * dc
            if run >= self.k:
                return True
        return False


class Game(TicTacToe):
    def __init__(self, size: int):
        self._n = size
        self._k = size
        self.reset()

    def set_win_length(self, k: int) -> None:
        if self._moves or not 3 <= k <= self._n:
            raise InvalidMove(f"win length {k}")
        self._k = k

    def reset(self) -> None:
        self._cells: list[list[Mark | None]] = [[None] * self._n for _ in range(self._n)]
        self._lines = _Lines(self._n)
        self._turn = 0
        self._moves = 0
        self._state = GameState.IN_PROGRESS

    def move(self, row: int, col: int) -> MoveOutcome:
        if self._state is not GameState.IN_PROGRESS:
            raise GameOver(self._state.name)
        if not (0 <= row < self._n and 0 <= col < self._n) or self._cells[row][col] is not None:
            raise InvalidMove(f"({row},{col})")
        mark = PLAYERS[self._turn]
        self._cells[row][col] = mark
        self._moves += 1
        won = (self._lines.add(row, col, 1 if mark is Mark.X else -1) if self._k == self._n
               else _Scan(self._cells, self._k).add(row, col, mark))
        if won:
            self._state = WIN_STATE[mark]
        elif self._moves == self._n * self._n:
            self._state = GameState.DRAW
        self._turn = (self._turn + 1) % len(PLAYERS)
        return MoveOutcome(mark, self._state)

    def current(self) -> Mark:
        if self._state is not GameState.IN_PROGRESS:
            raise GameOver(self._state.name)
        return PLAYERS[self._turn]

    def state(self) -> GameState:
        return self._state

    def board(self) -> list[str]:
        return ["".join(c.name if c else "." for c in row) for row in self._cells]
