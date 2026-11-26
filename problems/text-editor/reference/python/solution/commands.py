from __future__ import annotations

from abc import ABC, abstractmethod


class Buffer:
    """Text + cursor. Commands mutate it; a rope or gap buffer could replace the string."""

    def __init__(self):
        self.text = ""
        self.cursor = 0

    def insert_at(self, pos: int, s: str) -> None:
        self.text = self.text[:pos] + s + self.text[pos:]

    def delete_range(self, start: int, end: int) -> str:
        removed = self.text[start:end]
        self.text = self.text[:start] + self.text[end:]
        return removed


class Command(ABC):
    @abstractmethod
    def do(self, b: Buffer) -> None: ...

    @abstractmethod
    def undo(self, b: Buffer) -> None: ...


class Insert(Command):
    def __init__(self, pos: int, text: str):
        self.pos, self.text = pos, text

    def do(self, b):
        b.insert_at(self.pos, self.text)
        b.cursor = self.pos + len(self.text)

    def undo(self, b):
        b.delete_range(self.pos, self.pos + len(self.text))
        b.cursor = self.pos


class Backspace(Command):
    def __init__(self, end: int, n: int):
        self.end = end
        self.start = max(0, end - n)
        self.removed = ""

    def do(self, b):
        self.removed = b.delete_range(self.start, self.end)
        b.cursor = self.start

    def undo(self, b):
        b.insert_at(self.start, self.removed)
        b.cursor = self.end
