# Tic-Tac-Toe (N×N)

Design a Tic-Tac-Toe engine for an `N×N` board (N from config, ≥ 3).

## Requirements

1. `X` always moves first; players alternate.
2. `move(row, col)` (0-indexed) places the current player's mark and returns
   `{mark, state}`. Off the board or an occupied cell → `InvalidMove`. Any move after the
   game ended → `GameOver`.
3. A player wins by filling a whole row, a whole column, or either diagonal (all `N`
   cells). A full board with no winner is a `DRAW`. A move that fills the board *and* wins
   is a win.
4. `state()` is `IN_PROGRESS`, `X_WON`, `O_WON` or `DRAW`. `current()` is whose turn it is
   (`GameOver` once the game ended).
5. `board()` returns `N` strings, one per row, using `X`, `O` and `.` for empty.
6. `reset()` clears the board; `X` moves first again.
7. Detecting a win after a move should not rescan the whole board.

## Things an interviewer will push on

- How do you detect a win in O(1) per move?
- How would you support K-in-a-row on a bigger board, or more than two players?
- How would you plug in a computer player?
