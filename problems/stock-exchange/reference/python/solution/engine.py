from __future__ import annotations

import itertools
import threading

from contract import (BookView, Exchange, InvalidOrder, InvalidState, Level, OrderResult, OrderStatus, OrderType, Side,
                      Trade, UnknownOrder)

from .book import BookSide, Order

S = OrderStatus


def crosses(incoming: Order, resting_price: int) -> bool:
    if incoming.type is OrderType.MARKET:
        return True
    return resting_price <= incoming.price if incoming.side is Side.BUY else resting_price >= incoming.price


class SymbolBook:
    def __init__(self):
        self.sides = {Side.BUY: BookSide(best_is_highest=True), Side.SELL: BookSide(best_is_highest=False)}
        self.lock = threading.Lock()

    def match(self, incoming: Order) -> None:
        """One routine for both sides: walk the opposite side while prices cross."""
        opposite = self.sides[Side.SELL if incoming.side is Side.BUY else Side.BUY]
        while incoming.remaining:
            resting = opposite.best()
            if resting is None or not crosses(incoming, resting.price):
                break
            qty = min(incoming.remaining, resting.remaining)
            buy, sell = (incoming, resting) if incoming.side is Side.BUY else (resting, incoming)
            trade = Trade(buy.id, sell.id, resting.price, qty)
            for o in (incoming, resting):
                o.filled += qty
                o.trades.append(trade)
                o.status = S.FILLED if o.remaining == 0 else S.PARTIALLY_FILLED
            if resting.remaining == 0:
                opposite.pop_best()
        if incoming.remaining:
            if incoming.type is OrderType.MARKET:
                incoming.status = S.CANCELLED  # market orders never rest
            else:
                self.sides[incoming.side].add(incoming)


class MatchingEngine(Exchange):
    def __init__(self):
        self._books: dict[str, SymbolBook] = {}
        self._orders: dict[str, tuple[Order, SymbolBook]] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()  # registry only; matching locks per symbol

    @staticmethod
    def _view(o: Order) -> OrderResult:
        return OrderResult(o.id, o.status, o.filled, list(o.trades))

    def _book(self, symbol: str) -> SymbolBook:
        with self._lock:
            return self._books.setdefault(symbol, SymbolBook())

    def place_order(self, trader: str, symbol: str, side: Side, type: OrderType, qty: int, price: int) -> OrderResult:
        if qty < 1 or (type is OrderType.LIMIT and price < 1):
            raise InvalidOrder(f"qty={qty} price={price}")
        book = self._book(symbol)
        with self._lock:
            o = Order(f"O{next(self._ids)}", side, type, qty, price)
            self._orders[o.id] = (o, book)
        with book.lock:
            book.match(o)
            return self._view(o)

    def _lookup(self, order_id: str) -> tuple[Order, SymbolBook]:
        with self._lock:
            found = self._orders.get(order_id)
        if found is None:
            raise UnknownOrder(order_id)
        return found

    def cancel(self, order_id: str) -> OrderResult:
        o, book = self._lookup(order_id)
        with book.lock:
            if o.status not in (S.OPEN, S.PARTIALLY_FILLED):
                raise InvalidState(o.status.name)
            o.status = S.CANCELLED  # removed lazily from its level
            return self._view(o)

    def order(self, order_id: str) -> OrderResult:
        o, book = self._lookup(order_id)
        with book.lock:
            return self._view(o)

    def book(self, symbol: str) -> BookView:
        b = self._book(symbol)
        with b.lock:
            return BookView([Level(p, q) for p, q in b.sides[Side.BUY].levels()],
                            [Level(p, q) for p, q in b.sides[Side.SELL].levels()])
