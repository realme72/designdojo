from __future__ import annotations

from abc import ABC, abstractmethod

from contract import InvalidPromotion, PromoKind, Promotion


class ItemPromotion(ABC):
    def __init__(self, p: Promotion):
        self.code, self.sku = p.code, p.sku

    @abstractmethod
    def discount(self, qty: int, unit_price: int) -> int: ...


class CartPromotion(ABC):
    def __init__(self, p: Promotion):
        self.code, self.threshold = p.code, p.threshold

    def discount(self, amount: int) -> int:
        return self._discount(amount) if amount >= self.threshold else 0

    @abstractmethod
    def _discount(self, amount: int) -> int: ...


class PercentOffSku(ItemPromotion):
    def __init__(self, p):
        super().__init__(p)
        self.pct = p.value

    def discount(self, qty, unit_price):
        return qty * unit_price * self.pct // 100


class BuyXGetY(ItemPromotion):
    def __init__(self, p):
        super().__init__(p)
        self.x, self.y = p.threshold, p.value

    def discount(self, qty, unit_price):
        return (qty // (self.x + self.y)) * self.y * unit_price


class BundlePrice(ItemPromotion):
    def __init__(self, p):
        super().__init__(p)
        self.size, self.price = p.threshold, p.value

    def discount(self, qty, unit_price):
        return (qty // self.size) * max(0, self.size * unit_price - self.price)


class FlatOffCart(CartPromotion):
    def __init__(self, p):
        super().__init__(p)
        self.value = p.value

    def _discount(self, amount):
        return self.value


class PercentOffCart(CartPromotion):
    def __init__(self, p):
        super().__init__(p)
        self.pct = p.value

    def _discount(self, amount):
        return amount * self.pct // 100


def make_promotion(p: Promotion, known_skus: set[str]) -> ItemPromotion | CartPromotion:
    """Validation + construction in one place; adding a kind = one class + one entry."""
    builders = {
        PromoKind.PERCENT_OFF_SKU: (PercentOffSku, lambda: 1 <= p.value <= 100 and p.sku in known_skus),
        PromoKind.BUY_X_GET_Y: (BuyXGetY, lambda: p.threshold >= 1 and p.value >= 1 and p.sku in known_skus),
        PromoKind.BUNDLE_PRICE: (BundlePrice, lambda: p.threshold >= 1 and p.value >= 1 and p.sku in known_skus),
        PromoKind.FLAT_OFF_CART: (FlatOffCart, lambda: p.value >= 1),
        PromoKind.PERCENT_OFF_CART: (PercentOffCart, lambda: 1 <= p.value <= 100),
    }
    cls, valid = builders[p.kind]
    if not valid():
        raise InvalidPromotion(p.code)
    return cls(p)
