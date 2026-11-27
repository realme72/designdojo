# Chess

Design a chess engine that validates moves and detects check, checkmate and stalemate.
(No AI: two humans play.) **Castling and en passant are out of scope.**

## Requirements

1. Squares use algebraic notation `a1`…`h8`. Anything else → `InvalidSquare`.
2. Config `setup`: 8 strings from rank 8 down to rank 1, using `KQRBNP` (white), `kqrbnp`
   (black) and `.`; plus `to_move`. An empty `setup` means the standard starting position
   with white to move.
3. `move(from_sq, to_sq, promotion)`: moving nothing, the opponent's piece, a move the piece
   can't make (blocked paths, capturing your own piece…), or a move that leaves **your own
   king in check** → `IllegalMove`. After the game ended → `GameOver`.
   Returns `{captured, status}`: `captured` is the captured piece's letter or `""`.
4. Pieces move as in standard chess. Pawns: one step forward onto an empty square, two from
   their starting rank if both squares are empty, capture one step diagonally forward.
5. Promotion: a pawn reaching the last rank becomes `promotion` (`Q`, `R`, `B`, `N`, case
   ignored; `""` means queen). Anything else → `IllegalMove`.
6. `status()` describes the side to move: `CHECKMATE` (in check, no legal moves),
   `STALEMATE` (not in check, no legal moves), `CHECK`, or `IN_PROGRESS`.
   Checkmate and stalemate end the game.
7. `turn()`, `board()` (same format as `setup`), and `legal_moves(square)` → sorted target
   squares for a piece of the side to move (empty list for empty squares or the opponent's pieces).

## Things an interviewer will push on

- Piece hierarchy (polymorphic move generation) vs a table of direction vectors?
- Where does "doesn't leave your king in check" live, and how do you avoid rewriting it per piece?
- How would you add castling, en passant and undo?
