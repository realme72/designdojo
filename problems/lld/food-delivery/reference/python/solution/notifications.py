from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict

from contract import OrderStatus


class OrderListener(ABC):
    @abstractmethod
    def on_status(self, order_id: str, customer: str, status: OrderStatus) -> None: ...


class CustomerInbox(OrderListener):
    def __init__(self):
        self._messages: defaultdict[str, list[str]] = defaultdict(list)

    def on_status(self, order_id, customer, status):
        self._messages[customer].append(f"{order_id}:{status.name}")

    def messages(self, customer: str) -> list[str]:
        return list(self._messages.get(customer, []))
