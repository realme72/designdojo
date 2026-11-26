from __future__ import annotations

from abc import ABC, abstractmethod


class Schedule(ABC):
    @abstractmethod
    def after_run(self, now: int) -> int | None:
        """Next run after running at `now`; None = finished."""

    @abstractmethod
    def on_resume(self, now: int, current: int) -> int: ...


class Once(Schedule):
    def after_run(self, now):
        return None

    def on_resume(self, now, current):
        return current


class Every(Schedule):
    """Catch-up policy: run once, then the first slot strictly after now."""

    def __init__(self, start: int, interval: int):
        self.start, self.interval = start, interval

    def _slot_at_or_after(self, t: int) -> int:
        if t <= self.start:
            return self.start
        k = -(-(t - self.start) // self.interval)
        return self.start + k * self.interval

    def after_run(self, now):
        return self._slot_at_or_after(now + 1)

    def on_resume(self, now, current):
        return self._slot_at_or_after(now)


class Times(Every):
    """Every, but at most `times` runs."""

    def __init__(self, start: int, interval: int, times: int):
        super().__init__(start, interval)
        self.left = times

    def after_run(self, now):
        self.left -= 1
        return super().after_run(now) if self.left > 0 else None
