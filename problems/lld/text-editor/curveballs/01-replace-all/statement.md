# Replace all

Add `replace_all(find, replace)`: replaces every non-overlapping occurrence (left to right)
and returns how many were replaced. The cursor moves to the end of the content. It's **one**
undoable step: a single `undo` restores the previous content and cursor, and `redo` reapplies
it. Zero matches change nothing and record no step. An empty `find` raises `InvalidArgument`.

*Interviewer's question:* new Command, or a macro of existing ones?
