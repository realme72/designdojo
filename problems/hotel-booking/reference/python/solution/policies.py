from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date


class PricingPolicy(ABC):
    @abstractmethod
    def total(self, nightly_rate: int, check_in: date, check_out: date) -> int: ...


class NightlyPricing(PricingPolicy):
    def total(self, nightly_rate, check_in, check_out):
        return (check_out - check_in).days * nightly_rate


class RefundPolicy(ABC):
    @abstractmethod
    def refund(self, total: int, today: date, check_in: date) -> int: ...


class TwoDayRefund(RefundPolicy):
    def refund(self, total, today, check_in):
        return total if (check_in - today).days >= 2 else total // 2
