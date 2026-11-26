from __future__ import annotations

import threading
from collections import defaultdict

from contract import (Allocation, DuplicateOrder, InvalidQuantity, Inventory, Line, UnknownOrder, UnknownSku)

from .allocation import AllocationStrategy


class StockService(Inventory):
    def __init__(self, strategy: AllocationStrategy):
        self._strategy = strategy
        self._on_hand: dict[str, defaultdict[str, int]] = {}
        self._reserved: dict[str, defaultdict[str, int]] = {}
        self._orders: dict[str, list[Allocation]] = {}
        self._seen_orders: set[str] = set()
        self._thresholds: dict[str, int] = {}
        self._lock = threading.Lock()

    def _check(self, sku: str) -> None:
        if sku not in self._on_hand:
            raise UnknownSku(sku)

    def _free(self, sku: str) -> dict[str, int]:
        return {wh: n - self._reserved[sku][wh] for wh, n in self._on_hand[sku].items()}

    def receive(self, sku: str, warehouse: str, qty: int) -> None:
        if qty < 1:
            raise InvalidQuantity(qty)
        with self._lock:
            self._on_hand.setdefault(sku, defaultdict(int))[warehouse] += qty
            self._reserved.setdefault(sku, defaultdict(int))

    def available(self, sku: str) -> int:
        with self._lock:
            self._check(sku)
            return sum(self._free(sku).values())

    def available_at(self, sku: str, warehouse: str) -> int:
        with self._lock:
            self._check(sku)
            return self._free(sku).get(warehouse, 0)

    def reserve(self, order_id: str, lines: list[Line]) -> list[Allocation]:
        with self._lock:
            if order_id in self._seen_orders:
                raise DuplicateOrder(order_id)
            if not lines or any(l.qty < 1 for l in lines):
                raise InvalidQuantity("empty or non-positive line")
            for l in lines:
                self._check(l.sku)
            plan = self._strategy.plan(lines, {l.sku: self._free(l.sku) for l in lines})
            for a in plan:
                self._reserved[a.sku][a.warehouse] += a.qty
            self._orders[order_id] = plan
            self._seen_orders.add(order_id)
            return plan

    def _end(self, order_id: str) -> list[Allocation]:
        plan = self._orders.pop(order_id, None)
        if plan is None:
            raise UnknownOrder(order_id)
        for a in plan:
            self._reserved[a.sku][a.warehouse] -= a.qty
        return plan

    def commit(self, order_id: str) -> None:
        with self._lock:
            for a in self._end(order_id):
                self._on_hand[a.sku][a.warehouse] -= a.qty

    def release(self, order_id: str) -> None:
        with self._lock:
            self._end(order_id)

    def set_threshold(self, sku: str, threshold: int) -> None:
        with self._lock:
            self._check(sku)
            self._thresholds[sku] = threshold

    def low_stock(self) -> list[str]:
        with self._lock:
            return sorted(s for s, t in self._thresholds.items() if sum(self._free(s).values()) < t)
