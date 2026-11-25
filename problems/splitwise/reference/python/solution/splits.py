from __future__ import annotations

from abc import ABC, abstractmethod

from contract import InvalidSplit, Share


def distribute_leftover(base: list[int], total: int) -> list[int]:
    """Give the cents that integer division lost to the first shares, one each."""
    out = list(base)
    for i in range(total - sum(base)):
        out[i % len(out)] += 1
    return out


class SplitStrategy(ABC):
    @abstractmethod
    def owed(self, amount: int, shares: list[Share]) -> list[int]:
        """Cents owed by each share, in order. Raises InvalidSplit."""


class EqualSplit(SplitStrategy):
    def owed(self, amount, shares):
        return distribute_leftover([amount // len(shares)] * len(shares), amount)


class ExactSplit(SplitStrategy):
    def owed(self, amount, shares):
        values = [s.value for s in shares]
        if any(v < 0 for v in values) or sum(values) != amount:
            raise InvalidSplit("exact shares must be non-negative and sum to the amount")
        return values


class PercentSplit(SplitStrategy):
    def owed(self, amount, shares):
        pcts = [s.value for s in shares]
        if any(p < 0 for p in pcts) or sum(pcts) != 100:
            raise InvalidSplit("percentages must be non-negative and sum to 100")
        return distribute_leftover([amount * p // 100 for p in pcts], amount)
