from __future__ import annotations

from collections import deque

from contract import GameOver, Move, MoveResult, SnakeGame

DELTA = {Move.UP: (-1, 0), Move.DOWN: (1, 0), Move.LEFT: (0, -1), Move.RIGHT: (0, 1)}


class Game(SnakeGame):
    def __init__(self, rows: int, cols: int, food: list[tuple[int, int]]):
        self.rows, self.cols = rows, cols
        self.food = deque(food)
        self.snake: deque[tuple[int, int]] = deque([(0, 0)])  # head at the left
        self.occupied = {(0, 0)}
        self._score = 0
        self.alive = True
        self.wrap = False

    def set_wrap(self, enabled: bool) -> None:
        self.wrap = enabled

    def _next_head(self, r: int, c: int, dr: int, dc: int) -> tuple[int, int]:
        if self.wrap:
            return (r + dr) % self.rows, (c + dc) % self.cols
        return r + dr, c + dc

    def move(self, direction: Move) -> MoveResult:
        if not self.alive:
            raise GameOver()
        dr, dc = DELTA[direction]
        r, c = self.snake[0]
        head = self._next_head(r, c, dr, dc)
        eating = bool(self.food) and head == self.food[0]
        if not eating:  # the tail leaves this cell in the same move
            self.occupied.discard(self.snake.pop())
        inside = 0 <= head[0] < self.rows and 0 <= head[1] < self.cols
        if not inside or head in self.occupied:
            self.alive = False
            return MoveResult(self._score, False)
        if eating:
            self.food.popleft()
            self._score += 1
        self.snake.appendleft(head)
        self.occupied.add(head)
        return MoveResult(self._score, True)

    def body(self) -> list[list[int]]:
        return [list(cell) for cell in self.snake]

    def score(self) -> int:
        return self._score
