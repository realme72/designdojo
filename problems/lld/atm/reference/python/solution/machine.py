from __future__ import annotations

from contract import Atm, CannotDispense, InsufficientFunds, InvalidAmount, InvalidState, NoteBundle

from .bank import Bank
from .dispenser import Dispenser


class _State:
    """Base state: everything is illegal unless a state allows it."""

    def insert_card(self, atm, card): raise InvalidState("card already inserted")
    def enter_pin(self, atm, pin): raise InvalidState("no card awaiting PIN")
    def require_auth(self, atm): raise InvalidState("not authenticated")
    def eject(self, atm): raise InvalidState("no card")


class _NoCard(_State):
    def insert_card(self, atm, card):
        atm.bank.check_card(card)
        atm.card = card
        atm.state = CARD


class _CardInserted(_State):
    def enter_pin(self, atm, pin):
        try:
            atm.bank.verify(atm.card, pin)
        except Exception:
            if atm.bank_blocked():
                atm.end_session()
            raise
        atm.state = AUTH

    def eject(self, atm):
        atm.end_session()


class _Authenticated(_CardInserted):
    def enter_pin(self, atm, pin): raise InvalidState("already authenticated")
    def require_auth(self, atm): return None


NO_CARD, CARD, AUTH = _NoCard(), _CardInserted(), _Authenticated()


class AtmMachine(Atm):
    def __init__(self, bank: Bank, dispenser: Dispenser):
        self.bank = bank
        self.dispenser = dispenser
        self.card: str | None = None
        self.state: _State = NO_CARD

    def bank_blocked(self) -> bool:
        try:
            self.bank.check_card(self.card)
            return False
        except Exception:
            return True

    def end_session(self) -> None:
        self.card = None
        self.state = NO_CARD

    def insert_card(self, card: str) -> None:
        self.state.insert_card(self, card)

    def enter_pin(self, pin: str) -> None:
        self.state.enter_pin(self, pin)

    def eject(self) -> None:
        self.state.eject(self)

    def balance(self) -> int:
        self.state.require_auth(self)
        return self.bank.balance(self.card)

    def deposit(self, amount: int) -> int:
        self.state.require_auth(self)
        if amount <= 0:
            raise InvalidAmount(amount)
        return self.bank.adjust(self.card, amount)

    def withdraw(self, amount: int) -> list[NoteBundle]:
        self.state.require_auth(self)
        if amount <= 0:
            raise InvalidAmount(amount)
        if amount > self.bank.balance(self.card):
            raise InsufficientFunds(amount)
        plan = self.dispenser.plan(amount)
        if plan is None:
            raise CannotDispense(amount)
        self.bank.adjust(self.card, -amount)
        return self.dispenser.take(plan)

    def mini_statement(self):
        self.state.require_auth(self)
        return self.bank.recent(self.card)

    def cash(self) -> int:
        return self.dispenser.total()
