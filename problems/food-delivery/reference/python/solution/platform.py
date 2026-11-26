from __future__ import annotations

import itertools
import threading
from collections import deque
from dataclasses import dataclass

from contract import (FoodDelivery, InvalidCoupon, InvalidOrder, InvalidState, ItemUnavailable, Order, OrderLine, OrderStatus,
                      UnknownItem, UnknownOrder, UnknownRestaurant)

from .notifications import CustomerInbox, OrderListener

S = OrderStatus
TRANSITIONS = {
    S.PLACED: {S.ACCEPTED, S.REJECTED, S.CANCELLED},
    S.ACCEPTED: {S.READY, S.CANCELLED},
    S.READY: {S.OUT_FOR_DELIVERY},
    S.OUT_FOR_DELIVERY: {S.DELIVERED},
}
NEEDS_AGENT = {S.ACCEPTED, S.READY}


@dataclass
class MenuItem:
    price: int
    available: bool = True


@dataclass
class OrderRecord:
    id: str
    customer: str
    restaurant: str
    total: int
    status: OrderStatus = S.PLACED
    agent: str = ""
    subtotal: int = 0
    coupon: str = ""

    def view(self) -> Order:
        return Order(self.id, self.customer, self.restaurant, self.status, self.total, self.agent)


class Platform(FoodDelivery):
    def __init__(self, delivery_fee: int, listeners: list[OrderListener], inbox: CustomerInbox):
        self._fee = delivery_fee
        self._listeners = listeners
        self._inbox = inbox
        self._menus: dict[str, dict[str, MenuItem]] = {}
        self._orders: dict[str, OrderRecord] = {}
        self._free: set[str] = set()
        self._waiting: deque[str] = deque()
        self._ids = itertools.count(1)
        self._coupons: dict[str, tuple[int, int]] = {}  # code -> (percent, cap)
        self._lock = threading.RLock()

    # ---- catalog ----
    def _menu(self, rid: str) -> dict[str, MenuItem]:
        menu = self._menus.get(rid)
        if menu is None:
            raise UnknownRestaurant(rid)
        return menu

    def add_restaurant(self, restaurant_id: str) -> None:
        with self._lock:
            self._menus.setdefault(restaurant_id, {})

    def add_item(self, restaurant_id: str, item_id: str, price: int) -> None:
        with self._lock:
            self._menu(restaurant_id)[item_id] = MenuItem(price)

    def set_item_available(self, restaurant_id: str, item_id: str, available: bool) -> None:
        with self._lock:
            item = self._menu(restaurant_id).get(item_id)
            if item is None:
                raise UnknownItem(item_id)
            item.available = available

    # ---- agents ----
    def add_agent(self, agent_id: str) -> None:
        with self._lock:
            self._free.add(agent_id)
            self._dispatch_waiting()

    def _dispatch_waiting(self) -> None:
        while self._free and self._waiting:
            o = self._orders[self._waiting.popleft()]
            if o.status in NEEDS_AGENT and not o.agent:
                o.agent = min(self._free)
                self._free.discard(o.agent)

    def _release(self, o: OrderRecord) -> None:
        if o.agent:
            self._free.add(o.agent)
            self._dispatch_waiting()

    # ---- orders ----
    def _order(self, oid: str) -> OrderRecord:
        o = self._orders.get(oid)
        if o is None:
            raise UnknownOrder(oid)
        return o

    def _notify(self, o: OrderRecord) -> None:
        for listener in self._listeners:
            listener.on_status(o.id, o.customer, o.status)

    def _move(self, oid: str, to: OrderStatus) -> OrderRecord:
        o = self._order(oid)
        if to not in TRANSITIONS.get(o.status, ()):
            raise InvalidState(f"{o.status.name} -> {to.name}")
        o.status = to
        self._notify(o)
        return o

    def place_order(self, customer: str, restaurant_id: str, lines: list[OrderLine]) -> Order:
        with self._lock:
            menu = self._menu(restaurant_id)
            if not lines or any(l.qty < 1 for l in lines):
                raise InvalidOrder("empty order or bad quantity")
            total = self._fee
            for l in lines:
                item = menu.get(l.item_id)
                if item is None:
                    raise UnknownItem(l.item_id)
                if not item.available:
                    raise ItemUnavailable(l.item_id)
                total += item.price * l.qty
            o = OrderRecord(f"O{next(self._ids)}", customer, restaurant_id, total, subtotal=total - self._fee)
            self._orders[o.id] = o
            self._notify(o)
            return o.view()

    def add_coupon(self, code: str, percent_off: int, max_off: int) -> None:
        with self._lock:
            self._coupons[code] = (percent_off, max_off)

    def apply_coupon(self, order_id: str, code: str) -> Order:
        with self._lock:
            o = self._order(order_id)
            if o.status is not S.PLACED:
                raise InvalidState(f"{o.status.name}: coupons apply before acceptance")
            if code not in self._coupons or o.coupon:
                raise InvalidCoupon(code)
            percent, cap = self._coupons[code]
            o.total -= min(o.subtotal * percent // 100, cap)
            o.coupon = code
            return o.view()

    def accept(self, order_id: str) -> Order:
        with self._lock:
            o = self._move(order_id, S.ACCEPTED)
            self._waiting.append(o.id)
            self._dispatch_waiting()
            return o.view()

    def reject(self, order_id: str) -> Order:
        with self._lock:
            return self._move(order_id, S.REJECTED).view()

    def mark_ready(self, order_id: str) -> Order:
        with self._lock:
            return self._move(order_id, S.READY).view()

    def pick_up(self, order_id: str) -> Order:
        with self._lock:
            if not self._order(order_id).agent:
                raise InvalidState("no agent assigned yet")
            return self._move(order_id, S.OUT_FOR_DELIVERY).view()

    def deliver(self, order_id: str) -> Order:
        with self._lock:
            o = self._move(order_id, S.DELIVERED)
            self._release(o)
            return o.view()

    def cancel(self, order_id: str) -> Order:
        with self._lock:
            o = self._move(order_id, S.CANCELLED)
            self._release(o)
            return o.view()

    def order(self, order_id: str) -> Order:
        with self._lock:
            return self._order(order_id).view()

    def notifications(self, customer: str) -> list[str]:
        with self._lock:
            return self._inbox.messages(customer)

    def free_agents(self) -> int:
        with self._lock:
            return len(self._free)

    def waiting_orders(self) -> int:
        with self._lock:
            return sum(1 for o in self._orders.values() if o.status in NEEDS_AGENT and not o.agent)
