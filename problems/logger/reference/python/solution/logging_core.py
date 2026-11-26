from __future__ import annotations

import threading

from contract import Clock, DuplicateSink, Level, Logging, UnknownSink

from .sinks import Formatter, MemorySink, Record

ORDER = {lvl: i for i, lvl in enumerate(Level)}


class LogManager(Logging):
    def __init__(self, root_level: Level, clock: Clock):
        self._levels: dict[str, Level] = {"": root_level}
        self._sinks: dict[str, MemorySink] = {}
        self._clock = clock
        self._lock = threading.Lock()  # guards the registries; sinks lock their own output

    def effective_level(self, logger: str) -> Level:
        name = logger
        while True:
            if name in self._levels:
                return self._levels[name]
            if not name:
                return self._levels[""]
            name = name.rpartition(".")[0]

    def add_sink(self, name: str, min_level: Level, format: str) -> None:
        sink = MemorySink(min_level, Formatter(format))  # validates before registering
        with self._lock:
            if name in self._sinks:
                raise DuplicateSink(name)
            self._sinks[name] = sink

    def remove_sink(self, name: str) -> None:
        with self._lock:
            if self._sinks.pop(name, None) is None:
                raise UnknownSink(name)

    def set_level(self, logger: str, level: Level) -> None:
        with self._lock:
            self._levels[logger] = level

    def log(self, logger: str, level: Level, message: str) -> int:
        with self._lock:
            if ORDER[level] < ORDER[self.effective_level(logger)]:
                return 0
            sinks = list(self._sinks.values())
        record = Record(self._clock.now(), level, logger, message)
        written = 0
        for sink in sinks:
            if ORDER[level] >= ORDER[sink.min_level]:
                sink.write(sink.formatter.format(record))
                written += 1
        return written

    def output(self, name: str) -> list[str]:
        with self._lock:
            sink = self._sinks.get(name)
        if sink is None:
            raise UnknownSink(name)
        return sink.snapshot()
