from __future__ import annotations

from abc import ABC, abstractmethod

DAY = 86400


class FinePolicy(ABC):
    @abstractmethod
    def fine(self, due_at: int, returned_at: int) -> int: ...


class PerDayFine(FinePolicy):
    """Every started day late costs the same."""

    def __init__(self, per_day: int):
        self.per_day = per_day

    def fine(self, due_at, returned_at):
        late = returned_at - due_at
        return 0 if late <= 0 else -(-late // DAY) * self.per_day
