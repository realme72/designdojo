# Text Editor with Undo/Redo

Design the editing core of a text editor: a document with a cursor, clipboard, and
unlimited undo/redo.

## Requirements

1. The document starts empty with the cursor at 0. `content()` and `cursor()` report state.
2. `insert(text)` inserts at the cursor and moves the cursor to the end of the inserted text.
3. `backspace(n)` deletes up to `n` characters before the cursor and returns the deleted
   text (`n < 1` → `InvalidArgument`).
4. `move_cursor(pos)` moves the cursor; `pos` outside `0..len` → `InvalidPosition`.
   Cursor moves are **not** undoable.
5. `copy(start, end)` copies `content[start:end]` to the clipboard (bad range →
   `InvalidPosition`); `paste()` inserts the clipboard at the cursor (empty clipboard →
   no-op that is still not recorded).
6. `undo()` reverts the last edit (`insert`, `backspace`, `paste`) and restores the cursor
   to where it was before that edit. `redo()` re-applies the last undone edit and puts the
   cursor where that edit left it. Any new edit clears the redo history.
   Nothing to undo/redo → `NothingToUndo` / `NothingToRedo`.
7. Edits that change nothing (`insert("")`, `backspace` at position 0) are not recorded.

## Things an interviewer will push on

- Command objects vs snapshots (Memento) for undo: memory on a 1 GB file?
- Which data structure makes mid-document inserts cheap (gap buffer, rope, piece table)?
- How would you merge consecutive keystrokes into one undo step?
