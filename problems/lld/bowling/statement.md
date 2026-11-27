# Bowling Scorer

Score a single player's ten-pin bowling game, roll by roll.

## Requirements

1. `roll(pins)` records a roll. Invalid → `InvalidRoll`: `pins` outside 0–10, or more pins
   than are standing in the frame. After the game ends → `GameOver`.
2. Frames 1–9: a **strike** (10 on the first roll) ends the frame and scores 10 + the next
   two rolls; a **spare** (10 in two rolls) scores 10 + the next roll; otherwise the frame
   scores its pins.
3. Frame 10: a strike earns two bonus rolls, a spare one bonus roll. Pins are reset after
   each strike/spare in the 10th, so e.g. `X X X` and `X 7 /` and `7 / X` are valid, but
   `X 7 5` is not (only 3 pins were standing for the last roll).
4. `frame_scores()` returns the **cumulative** score after each frame whose score is final
   (its bonus rolls have been made), in order.
5. `score()` is the last final cumulative score (0 if none). `is_over()` reports whether all
   rolls of the game are done.

## Things an interviewer will push on

- Frame as an object, or a flat list of rolls with index arithmetic?
- Where does the 10th-frame special case live?
- How would you support multiple players or a different scoring variant?
