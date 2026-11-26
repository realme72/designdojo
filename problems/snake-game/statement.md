# Snake Game

Design the engine for the classic Snake game.

## Requirements

1. A `rows × cols` grid. The snake starts at `[0, 0]` with length 1.
2. Food appears one piece at a time, from the configured list in order; the next piece
   appears only after the current one is eaten.
3. `move(direction)` moves the head one cell. Returns `{score, alive}`:
   - Leaving the grid or running into its own body → the snake dies (`alive = false`).
   - The cell the tail is leaving in this same move is free (the head may move into it).
   - Eating food grows the snake by one (the tail stays) and adds 1 to the score.
   - Any move after death → `GameOver`.
4. `body()` returns the snake's cells, head first. `score()` returns the score.
5. Moves must be O(1).

## Things an interviewer will push on

- Which structures give O(1) moves and O(1) collision checks?
- How would you add obstacles, wrap-around walls or a second snake?
- Where does the "tail moves out first" rule live?
