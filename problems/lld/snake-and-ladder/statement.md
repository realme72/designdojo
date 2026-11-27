# Snake and Ladder

Design a multiplayer Snake and Ladder game engine. Dice rolls are passed in (the caller
owns randomness), so the engine itself is deterministic.

## Requirements

1. The board has squares `1..size`, plus snakes (`head → tail`, going down) and ladders
   (`bottom → top`, going up) from config. Boards never chain (a snake or ladder never ends
   on another one's start).
2. `add_player(name)` joins in order; turn order is join order. Joining after the first
   move → `GameStarted`; a repeated name → `DuplicatePlayer`.
3. Everyone starts at position 0 (off the board).
4. `move(player, roll)`:
   - Checks, in order: game already won → `GameOver`; unknown player → `UnknownPlayer`;
     not that player's turn → `NotYourTurn`; roll outside 1–6 → `InvalidRoll`.
   - Target = position + roll. Beyond `size` → the player stays put.
   - Landing on a snake head or ladder bottom moves the player to its end.
   - Landing exactly on `size` wins; the game is over.
   - Rolling a 6 gives the same player another turn (unless they just won). Otherwise
     the turn passes to the next player.
   - Returns `{player, roll, from_pos, to_pos, won, next_player}`; `next_player` is
     empty once the game is won.
5. `position(player)`, `current_player()` (no players → `NoPlayers`; game won →
   `GameOver`) and `winner()` (empty string while the game is on).

## Things an interviewer will push on

- Are snakes and ladders two classes, or one concept?
- How would you add special squares (skip a turn, teleport)?
- How would you plug in a different dice (two dice, loaded dice for tests)?
