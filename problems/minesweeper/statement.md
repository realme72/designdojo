# Minesweeper

Design a Minesweeper engine. Mine positions come from config (the caller owns randomness).

## Requirements

1. Board `rows × cols` with mines at the given `[row, col]` positions (0-indexed).
2. `reveal(row, col)`: off-board → `InvalidMove`; flagged or already revealed cell →
   `InvalidMove`; game over → `GameOver`.
   - A mine → the game is `LOST`.
   - A number cell (adjacent mines > 0) reveals just that cell.
   - A zero cell reveals itself and **flood-fills** all connected zero cells plus their
     bordering number cells (8-directional). Flagged cells are never auto-revealed.
   - Returns how many cells this call revealed.
3. `toggle_flag(row, col)` flags/unflags a hidden cell (revealed → `InvalidMove`).
4. The game is `WON` once every non-mine cell is revealed. `state()` is `PLAYING`, `WON` or `LOST`.
5. `view()` returns one string per row: `#` hidden, `F` flagged, `0`–`8` revealed counts,
   `*` for every mine once the game is lost.

## Things an interviewer will push on

- BFS vs DFS for flood fill: stack depth on a 1000×1000 board?
- Cell as an object vs parallel arrays?
- How would you guarantee the first click is never a mine?
