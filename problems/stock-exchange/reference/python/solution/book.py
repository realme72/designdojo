from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field

from contract import OrderStatus, OrderType, Side, Trade


@dataclass
class Order:
    id: str
    side: Side
    type: OrderType
    qty: int
    price: int
    filled: int = 0
    status: OrderStatus = OrderStatus.OPEN
    trades: list[Trade] = field(default_factory=list)

    @property
    def remaining(self) -> int:
        return self.qty - self.filled


class BookSide:
    """Price levels in a heap (best first) with a FIFO deque per level."""

    def __init__(self, best_is_highest: bool):
        self._sign = -1 if best_is_highest else 1
        self._heap: list[int] = []
        self._levels: dict[int, deque[Order]] = {}

    def add(self, o: Order) -> None:
        if o.price not in self._levels:
            self._levels[o.price] = deque()
            heapq.heappush(self._heap, self._sign * o.price)
        self._levels[o.price].append(o)

    def best(self) -> Order | None:
        while self._heap:
            price = self._sign * self._heap[0]
            level = self._levels.get(price)
            while level and level[0].status is OrderStatus.CANCELLED:
                level.popleft()  # lazy removal of cancelled orders
            if level:
                return level[0]
            heapq.heappop(self._heap)
            self._levels.pop(price, None)
        return None

    def pop_best(self) -> None:
        price = self._sign * self._heap[0]
        self._levels[price].popleft()

    def levels(self) -> list[tuple[int, int]]:
        out = []
        for price in sorted(self._levels, key=lambda p: self._sign * p):
            qty = sum(o.remaining for o in self._levels[price] if o.status is not OrderStatus.CANCELLED)
            if qty:
                out.append((price, qty))
        return out
