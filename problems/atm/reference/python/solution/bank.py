from __future__ import annotations

from contract import Account, CardBlocked, UnknownCard, WrongPin

MAX_ATTEMPTS = 3


class Bank:
    """Owns accounts and PIN verification, including the lockout rule."""

    def __init__(self, accounts: list[Account]):
        self._accounts = {a.card: {"pin": a.pin, "balance": a.balance} for a in accounts}
        self._failures: dict[str, int] = {}
        self._blocked: set[str] = set()

    def check_card(self, card: str) -> None:
        if card not in self._accounts:
            raise UnknownCard(card)
        if card in self._blocked:
            raise CardBlocked(card)

    def verify(self, card: str, pin: str) -> None:
        if self._accounts[card]["pin"] == pin:
            self._failures[card] = 0
            return
        self._failures[card] = self._failures.get(card, 0) + 1
        if self._failures[card] >= MAX_ATTEMPTS:
            self._blocked.add(card)
            raise CardBlocked(card)
        raise WrongPin(card)

    def balance(self, card: str) -> int:
        return self._accounts[card]["balance"]

    def adjust(self, card: str, delta: int) -> int:
        self._accounts[card]["balance"] += delta
        return self._accounts[card]["balance"]
