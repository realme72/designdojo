# Chording

Experienced players "chord": `chord(row, col)` on an **open** number cell whose adjacent flag
count equals its number reveals every hidden, unflagged neighbour at once (with the usual
flood fill for zeros) and returns how many cells opened. If a wrongly placed flag means a mine
gets revealed, the game is lost (return 0). Chording a cell that isn't open, or whose flag count
doesn't match, raises `InvalidMove`.

*Interviewer's question:* how much of reveal did you reuse?
