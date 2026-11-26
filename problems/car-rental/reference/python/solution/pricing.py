from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from contract import Bill


@dataclass(frozen=True)
class Trip:
    daily_rate: int
    booked_days: int
    late_days: int
    km: int


class FeeRule(ABC):
    line: str

    @abstractmethod
    def amount(self, t: Trip) -> int: ...


class BaseFee(FeeRule):
    line = "base"

    def amount(self, t):
        return t.booked_days * t.daily_rate


class LateFee(FeeRule):
    line = "late_fee"

    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    def amount(self, t):
        return t.late_days * t.daily_rate * self.multiplier


class MileageFee(FeeRule):
    line = "mileage_fee"

    def __init__(self, free_per_day: int, per_km: int):
        self.free_per_day, self.per_km = free_per_day, per_km

    def amount(self, t):
        return max(0, t.km - self.free_per_day * t.booked_days) * self.per_km


class Pricing:
    def __init__(self, rules: list[FeeRule]):
        self.rules = rules

    def bill(self, t: Trip) -> Bill:
        lines = {r.line: r.amount(t) for r in self.rules}
        return Bill(lines.get("base", 0), lines.get("late_fee", 0), lines.get("mileage_fee", 0), sum(lines.values()))
