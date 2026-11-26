from __future__ import annotations

from abc import ABC, abstractmethod

import threading

from contract import InvalidCap, SpotSize

HOUR = 3600
DAY_HOURS = 24


class PricingPolicy(ABC):
    """How a stay is charged. New rules (weekend rates, EV surcharge) are new implementations."""

    @abstractmethod
    def fee_cents(self, size: SpotSize, entry: int, exit_: int) -> int: ...


class HourlyPricing(PricingPolicy):
    """Whole hours, rounded up, minimum one, at the spot size's rate."""

    def __init__(self, rate_cents: dict[SpotSize, int]):
        missing = [s for s in SpotSize if s not in rate_cents]
        if missing:
            raise ValueError(f"missing rates for {missing}")
        self._rates = dict(rate_cents)

    def hours(self, entry: int, exit_: int) -> int:
        return max(1, -(-max(0, exit_ - entry) // HOUR))

    def rate(self, size: SpotSize) -> int:
        return self._rates[size]

    def fee_cents(self, size: SpotSize, entry: int, exit_: int) -> int:
        return self.hours(entry, exit_) * self._rates[size]


class DailyCapPricing(PricingPolicy):
    """Decorator: caps each 24-hour block (and the remainder) per spot size."""

    def __init__(self, inner: HourlyPricing):
        self._inner = inner
        self._caps: dict[SpotSize, int] = {}
        self._lock = threading.Lock()

    def set_cap(self, size: SpotSize, cap: int) -> None:
        if cap < 1:
            raise InvalidCap(cap)
        with self._lock:
            self._caps[size] = cap

    def fee_cents(self, size: SpotSize, entry: int, exit_: int) -> int:
        with self._lock:
            cap = self._caps.get(size)
        if cap is None:
            return self._inner.fee_cents(size, entry, exit_)
        hours, rate = self._inner.hours(entry, exit_), self._inner.rate(size)
        days, rest = divmod(hours, DAY_HOURS)
        return days * min(DAY_HOURS * rate, cap) + (min(rest * rate, cap) if rest else 0)
