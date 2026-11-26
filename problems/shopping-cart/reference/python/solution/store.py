from __future__ import annotations

from dataclasses import dataclass, field

from contract import (Bill, BillLine, DuplicatePromotion, InvalidCoupon, InvalidPrice, InvalidQuantity, NotInCart,
                      Promotion, Store, UnknownProduct, UnknownPromotion)

from .promotions import CartPromotion, ItemPromotion, make_promotion


@dataclass
class Cart:
    qty: dict[str, int] = field(default_factory=dict)
    coupon: str | None = None


class OnlineStore(Store):
    def __init__(self):
        self._prices: dict[str, int] = {}
        self._carts: dict[str, Cart] = {}
        self._item_promos: dict[str, list[ItemPromotion]] = {}
        self._promos: dict[str, ItemPromotion | CartPromotion] = {}

    def _cart(self, cart_id: str) -> Cart:
        return self._carts.setdefault(cart_id, Cart())

    def add_product(self, sku: str, name: str, price: int) -> None:
        if price < 1:
            raise InvalidPrice(price)
        self._prices[sku] = price

    def add_to_cart(self, cart_id: str, sku: str, qty: int) -> None:
        if sku not in self._prices:
            raise UnknownProduct(sku)
        if qty < 1:
            raise InvalidQuantity(qty)
        cart = self._cart(cart_id)
        cart.qty[sku] = cart.qty.get(sku, 0) + qty

    def remove_from_cart(self, cart_id: str, sku: str, qty: int) -> None:
        if qty < 1:
            raise InvalidQuantity(qty)
        cart = self._cart(cart_id)
        if sku not in cart.qty:
            raise NotInCart(sku)
        cart.qty[sku] -= qty
        if cart.qty[sku] <= 0:
            del cart.qty[sku]

    def add_promotion(self, promo: Promotion) -> None:
        if promo.code in self._promos:
            raise DuplicatePromotion(promo.code)
        p = make_promotion(promo, set(self._prices))
        self._promos[promo.code] = p
        if isinstance(p, ItemPromotion):
            self._item_promos.setdefault(p.sku, []).append(p)

    def apply_coupon(self, cart_id: str, code: str) -> None:
        p = self._promos.get(code)
        if p is None:
            raise UnknownPromotion(code)
        if not isinstance(p, CartPromotion):
            raise InvalidCoupon(code)
        self._cart(cart_id).coupon = code

    def bill(self, cart_id: str) -> Bill:
        cart = self._cart(cart_id)
        lines, subtotal, discount = [], 0, 0
        for sku in sorted(cart.qty):
            qty, price = cart.qty[sku], self._prices[sku]
            lines.append(BillLine(sku, qty, price, qty * price))
            subtotal += qty * price
            discount += max((p.discount(qty, price) for p in self._item_promos.get(sku, [])), default=0)
        if cart.coupon:
            discount += self._promos[cart.coupon].discount(subtotal - discount)
        discount = min(discount, subtotal)
        return Bill(subtotal, discount, subtotal - discount, lines)

    def checkout(self, cart_id: str) -> Bill:
        bill = self.bill(cart_id)
        self._carts[cart_id] = Cart()
        return bill
