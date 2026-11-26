from __future__ import annotations

from contract import Editor, InvalidArgument, InvalidPosition, NothingToRedo, NothingToUndo

from .commands import Backspace, Buffer, Command, Insert


class TextEditor(Editor):
    def __init__(self):
        self._buf = Buffer()
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self._clipboard = ""

    def _run(self, cmd: Command) -> None:
        cmd.do(self._buf)
        self._undo.append(cmd)
        self._redo.clear()

    def insert(self, text: str) -> None:
        if text:
            self._run(Insert(self._buf.cursor, text))

    def backspace(self, n: int) -> str:
        if n < 1:
            raise InvalidArgument(n)
        if self._buf.cursor == 0:
            return ""
        cmd = Backspace(self._buf.cursor, n)
        self._run(cmd)
        return cmd.removed

    def move_cursor(self, pos: int) -> None:
        if not 0 <= pos <= len(self._buf.text):
            raise InvalidPosition(pos)
        self._buf.cursor = pos

    def copy(self, start: int, end: int) -> None:
        if not 0 <= start <= end <= len(self._buf.text):
            raise InvalidPosition(f"{start}:{end}")
        self._clipboard = self._buf.text[start:end]

    def paste(self) -> None:
        self.insert(self._clipboard)

    def undo(self) -> None:
        if not self._undo:
            raise NothingToUndo()
        cmd = self._undo.pop()
        cmd.undo(self._buf)
        self._redo.append(cmd)

    def redo(self) -> None:
        if not self._redo:
            raise NothingToRedo()
        cmd = self._redo.pop()
        cmd.do(self._buf)
        self._undo.append(cmd)

    def content(self) -> str:
        return self._buf.text

    def cursor(self) -> int:
        return self._buf.cursor
