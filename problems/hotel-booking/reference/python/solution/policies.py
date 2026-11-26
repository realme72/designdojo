from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta


class PricingPolicy(ABC):
    @abstractmethod
    def total(self, nightly_rate: int, check_in: date, check_out: date) -> int: ...


class NightlyPricing(PricingPolicy):
    def total(self, nightly_rate, check_in, check_out):
        return (check_out - check_in).days * nightly_rate


class SeasonalPricing(PricingPolicy):
    """Per-night rate with seasonal percentages per room type; the latest matching season wins."""

    def __init__(self):
        self._seasons: list[tuple[object, date, date, int]] = []

    def add_season(self, room_type, start: date, end: date, percent: int) -> None:
        self._seasons.append((room_type, start, end, percent))

    def total(self, nightly_rate, check_in, check_out, room_type=None):
        total, night = 0, check_in
        while night < check_out:
            pct = next((p for t, s, e, p in reversed(self._seasons) if t is room_type and s <= night < e), 100)
            total += nightly_rate * pct // 100
            night += timedelta(days=1)
        return total


class RefundPolicy(ABC):
    @abstractmethod
    def refund(self, total: int, today: date, check_in: date) -> int: ...


class TwoDayRefund(RefundPolicy):
    def refund(self, total, today, check_in):
        return total if (check_in - today).days >= 2 else total // 2
