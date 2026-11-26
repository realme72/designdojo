from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62(n: int) -> str:
    out = ""
    while n:
        n, r = divmod(n, 62)
        out = ALPHABET[r] + out
    return out or "0"


class CodeGenerator(ABC):
    @abstractmethod
    def next_code(self, taken: Callable[[str], bool]) -> str: ...


class Base62Sequence(CodeGenerator):
    """Not thread-safe on its own: the service calls it under its lock."""

    def __init__(self, width: int):
        self.width = width
        self.n = 0

    def next_code(self, taken):
        while True:
            self.n += 1
            code = base62(self.n).rjust(self.width, "0")
            if not taken(code):
                return code
