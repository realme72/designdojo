from __future__ import annotations

import itertools
import threading

from contract import (Balance, DuplicateUser, InvalidAmount, InvalidSplit, Share, Splitwise, SplitType, Transfer,
                      UnknownUser)

from .splits import SplitStrategy


def plan_settlement(balances: dict[str, int]) -> list[Transfer]:
    """Greedy: largest creditor with largest debtor. Pure function over a snapshot."""
    bal = {u: a for u, a in balances.items() if a}
    out = []
    while bal:
        creditor = min((u for u in bal if bal[u] > 0), key=lambda u: (-bal[u], u))
        debtor = min((u for u in bal if bal[u] < 0), key=lambda u: (bal[u], u))
        amt = min(bal[creditor], -bal[debtor])
        out.append(Transfer(debtor, creditor, amt))
        for u, d in ((creditor, -amt), (debtor, amt)):
            bal[u] += d
            if not bal[u]:
                del bal[u]
    return out


class SplitwiseApp(Splitwise):
    def __init__(self, strategies: dict[SplitType, SplitStrategy]):
        self._strategies = strategies
        self._balances: dict[str, int] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def _known(self, *users: str) -> None:
        for u in users:
            if u not in self._balances:
                raise UnknownUser(u)

    def add_user(self, user_id: str) -> None:
        with self._lock:
            if user_id in self._balances:
                raise DuplicateUser(user_id)
            self._balances[user_id] = 0

    def add_expense(self, paid_by: str, amount: int, split_type: SplitType, shares: list[Share]) -> str:
        with self._lock:
            self._known(paid_by, *(s.user for s in shares))
            if amount <= 0 or not shares or len({s.user for s in shares}) != len(shares):
                raise InvalidSplit("amount must be positive and users unique")
            owed = self._strategies[split_type].owed(amount, shares)  # validates before any change
            self._balances[paid_by] += amount
            for s, cents in zip(shares, owed):
                self._balances[s.user] -= cents
            return f"E{next(self._ids)}"

    def settle(self, from_user: str, to_user: str, amount: int) -> None:
        with self._lock:
            self._known(from_user, to_user)
            if amount <= 0 or from_user == to_user:
                raise InvalidAmount(amount)
            self._balances[from_user] += amount
            self._balances[to_user] -= amount

    def balance(self, user_id: str) -> int:
        with self._lock:
            self._known(user_id)
            return self._balances[user_id]

    def balances(self) -> list[Balance]:
        with self._lock:
            return [Balance(u, a) for u, a in sorted(self._balances.items())]

    def simplify(self) -> list[Transfer]:
        with self._lock:
            snapshot = dict(self._balances)
        return plan_settlement(snapshot)
