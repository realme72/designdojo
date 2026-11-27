from __future__ import annotations

from dataclasses import dataclass

from contract import (CannotMakeChange, Coin, InsufficientFunds, InvalidProduct, SoldOut, UnknownProduct, Vend,
                      VendingMachine)

from .coins import VALUE, CoinBox, by_value_desc


@dataclass
class Product:
    name: str
    price: int
    quantity: int


class Machine(VendingMachine):
    def __init__(self, float_: dict[Coin, int]):
        self._box = CoinBox(float_)
        self._products: dict[str, Product] = {}
        self._session: list[Coin] = []

    def add_product(self, code: str, name: str, price: int, quantity: int) -> None:
        if price < 1 or quantity < 0:
            raise InvalidProduct(code)
        p = self._products.get(code)
        if p is None:
            self._products[code] = Product(name, price, quantity)
        else:
            p.name, p.price, p.quantity = name, price, p.quantity + quantity

    def insert(self, coin: Coin) -> int:
        self._session.append(coin)
        self._box.add(coin)
        return self.balance()

    def balance(self) -> int:
        return sum(VALUE[c] for c in self._session)

    def _product(self, code: str) -> Product:
        p = self._products.get(code)
        if p is None:
            raise UnknownProduct(code)
        return p

    def select(self, code: str) -> Vend:
        p = self._product(code)
        if p.quantity == 0:
            raise SoldOut(code)
        paid = self.balance()
        if paid < p.price:
            raise InsufficientFunds(f"{paid} < {p.price}")
        change = self._box.make_change(paid - p.price)
        if change is None:
            raise CannotMakeChange(paid - p.price)
        # all checks passed: now mutate
        p.quantity -= 1
        self._box.remove(change)
        self._session.clear()
        return Vend(code, by_value_desc(change))

    def cancel(self) -> list[Coin]:
        coins = by_value_desc(self._session)
        self._box.remove(coins)
        self._session.clear()
        return coins

    def stock(self, code: str) -> int:
        return self._product(code).quantity
