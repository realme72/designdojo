from __future__ import annotations

import json
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass

from contract import InvalidFormat, Level

PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
FIELDS = {"time", "level", "logger", "message"}


@dataclass(frozen=True)
class Record:
    time: int
    level: Level
    logger: str
    message: str


class Formatter:
    """Template parsed once; substitutes fields without re-interpreting their contents."""

    def __init__(self, template: str):
        bad = [m for m in PLACEHOLDER.findall(template) if m not in FIELDS]
        if bad:
            raise InvalidFormat(f"unknown placeholder(s): {bad}")
        self._parts = PLACEHOLDER.split(template)  # literal, field, literal, field, ...

    def format(self, r: Record) -> str:
        values = {"time": str(r.time), "level": r.level.name, "logger": r.logger, "message": r.message}
        return "".join(p if i % 2 == 0 else values[p] for i, p in enumerate(self._parts))


class JsonFormatter:
    """Compact JSON object per record, fixed key order."""

    def format(self, r: Record) -> str:
        return json.dumps({"time": r.time, "level": r.level.name, "logger": r.logger, "message": r.message},
                          separators=(",", ":"), ensure_ascii=False)


class Sink(ABC):
    def __init__(self, min_level: Level, formatter: Formatter | JsonFormatter):
        self.min_level = min_level
        self.formatter = formatter

    @abstractmethod
    def write(self, line: str) -> None: ...


class MemorySink(Sink):
    def __init__(self, min_level: Level, formatter: Formatter | JsonFormatter):
        super().__init__(min_level, formatter)
        self.lines: list[str] = []
        self._lock = threading.Lock()

    def write(self, line: str) -> None:
        with self._lock:
            self.lines.append(line)

    def snapshot(self) -> list[str]:
        with self._lock:
            return list(self.lines)
