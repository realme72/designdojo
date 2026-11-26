# Undo

Add `undo()`: take back the last move, restoring the board (including any captured piece or
promoted pawn), the side to move and the status. Undo works repeatedly, and also after
checkmate. With no move to undo, raise `IllegalMove`.

*Interviewer's question:* Command or Memento, and what does each cost here?
