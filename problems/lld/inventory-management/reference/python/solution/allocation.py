from __future__ import annotations

from abc import ABC, abstractmethod

from contract import Allocation, Line, OutOfStock


class AllocationStrategy(ABC):
    @abstractmethod
    def plan(self, lines: list[Line], free: dict[str, dict[str, int]]) -> list[Allocation]:
        """free: sku -> warehouse -> available. Must not mutate it. Raises OutOfStock."""


class WarehouseOrder(AllocationStrategy):
    """Fill each line from warehouses in name order."""

    def order(self, warehouses):
        return sorted(warehouses)

    def plan(self, lines, free):
        left = {sku: dict(whs) for sku, whs in free.items()}
        out: list[Allocation] = []
        for line in lines:
            need = line.qty
            for wh in self.order(left[line.sku]):
                take = min(need, left[line.sku][wh])
                if take:
                    out.append(Allocation(line.sku, wh, take))
                    left[line.sku][wh] -= take
                    need -= take
                if not need:
                    break
            if need:
                raise OutOfStock(line.sku)
        return out


class PriorityOrder(WarehouseOrder):
    """Prioritised warehouses first (lowest number), then the rest; ties by name."""

    def __init__(self):
        self.priorities: dict[str, int] = {}

    def order(self, warehouses):
        return sorted(warehouses, key=lambda w: (w not in self.priorities, self.priorities.get(w, 0), w))
