from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque

from contract import Algorithm


class Limiter(ABC):
    """One client's limiter. Not thread-safe by itself; the caller serialises per client."""

    @abstractmethod
    def allow(self, now: int) -> bool: ...


class FixedWindow(Limiter):
    def __init__(self, limit: int, window: int):
        self.limit, self.window = limit, window
        self.current, self.count = None, 0

    def allow(self, now):
        w = now // self.window
        if w != self.current:
            self.current, self.count = w, 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class SlidingLog(Limiter):
    def __init__(self, limit: int, window: int):
        self.limit, self.window = limit, window
        self.log: deque[int] = deque()

    def allow(self, now):
        while self.log and self.log[0] <= now - self.window:
            self.log.popleft()
        if len(self.log) < self.limit:
            self.log.append(now)
            return True
        return False


class TokenBucket(Limiter):
    """Tokens are stored scaled by `window` so refills stay exact integers."""

    def __init__(self, limit: int, window: int, now: int):
        self.limit, self.window = limit, window
        self.scaled = limit * window  # full
        self.last = now

    def allow(self, now):
        self.scaled = min(self.limit * self.window, self.scaled + (now - self.last) * self.limit)
        self.last = now
        if self.scaled >= self.window:
            self.scaled -= self.window
            return True
        return False


class SlidingCounter(Limiter):
    """Two aligned fixed-window counters; the previous one weighted by how much of it still overlaps."""

    def __init__(self, limit: int, window: int):
        self.limit, self.window = limit, window
        self.current, self.curr, self.prev = None, 0, 0

    def allow(self, now):
        w = now // self.window
        if w != self.current:
            self.prev = self.curr if self.current is not None and w == self.current + 1 else 0
            self.current, self.curr = w, 0
        elapsed = now - w * self.window
        if self.prev * (self.window - elapsed) + self.curr * self.window < self.limit * self.window:
            self.curr += 1
            return True
        return False


def make_limiter(algorithm: Algorithm, limit: int, window: int, now: int) -> Limiter:
    if algorithm is Algorithm.FIXED_WINDOW:
        return FixedWindow(limit, window)
    if algorithm is Algorithm.SLIDING_WINDOW_LOG:
        return SlidingLog(limit, window)
    if algorithm is Algorithm.SLIDING_WINDOW_COUNTER:
        return SlidingCounter(limit, window)
    return TokenBucket(limit, window, now)
