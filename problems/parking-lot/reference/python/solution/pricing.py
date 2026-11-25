from __future__ import annotations

from abc import ABC, abstractmethod

from contract import SpotSize

HOUR = 3600


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

    def fee_cents(self, size: SpotSize, entry: int, exit_: int) -> int:
        seconds = max(0, exit_ - entry)
        hours = max(1, -(-seconds // HOUR))
        return hours * self._rates[size]
