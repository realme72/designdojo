from __future__ import annotations

from contract import Coin

VALUE = {Coin.ONE: 1, Coin.TWO: 2, Coin.FIVE: 5, Coin.TEN: 10}
DESC = sorted(VALUE, key=VALUE.get, reverse=True)


def by_value_desc(coins: list[Coin]) -> list[Coin]:
    return sorted(coins, key=VALUE.get, reverse=True)


class CoinBox:
    """Coins held by the machine, and exact change-making with the fewest coins."""

    def __init__(self, initial: dict[Coin, int]):
        self.count = {c: initial.get(c, 0) for c in DESC}

    def add(self, coin: Coin) -> None:
        self.count[coin] += 1

    def remove(self, coins: list[Coin]) -> None:
        for c in coins:
            self.count[c] -= 1

    def make_change(self, amount: int) -> list[Coin] | None:
        """Fewest coins; ties prefer higher coins (DESC order explored high-count first)."""
        best: list[Coin] | None = None

        def go(i: int, remaining: int, picked: list[Coin]) -> None:
            nonlocal best
            if remaining == 0:
                if best is None or len(picked) < len(best):
                    best = list(picked)
                return
            if i == len(DESC) or (best is not None and len(picked) >= len(best)):
                return
            coin = DESC[i]
            most = min(self.count[coin], remaining // VALUE[coin])
            for k in range(most, -1, -1):
                go(i + 1, remaining - k * VALUE[coin], picked + [coin] * k)

        go(0, amount, [])
        return best
