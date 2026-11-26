from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field

from contract import (AlreadyReversed, DuplicateWallet, Entry, EntryType, IdempotencyConflict, InsufficientFunds,
                      InvalidAmount, LimitExceeded, SameWallet, Transaction, UnknownTransaction, UnknownWallet,
                      WalletService)


@dataclass
class Wallet:
    user: str
    balance: int = 0
    ledger: list[Entry] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def post(self, kind: EntryType, amount: int, delta: int) -> int:
        self.balance += delta
        self.ledger.append(Entry(kind, amount, self.balance))
        return self.balance


class Wallets(WalletService):
    def __init__(self, max_transfer: int):
        self._max = max_transfer
        self._wallets: dict[str, Wallet] = {}
        self._registry = threading.Lock()
        self._keys: dict[str, tuple[tuple, Transaction]] = {}
        self._keys_lock = threading.Lock()  # one in-flight transfer per key at a time
        self._key_locks: dict[str, threading.Lock] = {}
        self._ids = itertools.count(1)
        self._txns: dict[str, Transaction] = {}
        self._reversed: set[str] = set()
        self._txn_lock = threading.Lock()

    def _wallet(self, user: str) -> Wallet:
        with self._registry:
            w = self._wallets.get(user)
        if w is None:
            raise UnknownWallet(user)
        return w

    def create_wallet(self, user: str) -> None:
        with self._registry:
            if user in self._wallets:
                raise DuplicateWallet(user)
            self._wallets[user] = Wallet(user)

    def deposit(self, user: str, amount: int) -> int:
        w = self._wallet(user)
        if amount <= 0:
            raise InvalidAmount(amount)
        with w.lock:
            return w.post(EntryType.DEPOSIT, amount, amount)

    def withdraw(self, user: str, amount: int) -> int:
        w = self._wallet(user)
        if amount <= 0:
            raise InvalidAmount(amount)
        with w.lock:
            if amount > w.balance:
                raise InsufficientFunds(user)
            return w.post(EntryType.WITHDRAWAL, amount, -amount)

    def _key_lock(self, key: str) -> threading.Lock:
        with self._keys_lock:
            return self._key_locks.setdefault(key, threading.Lock())

    def transfer(self, from_user: str, to_user: str, amount: int, idempotency_key: str) -> Transaction:
        src, dst = self._wallet(from_user), self._wallet(to_user)
        if amount <= 0:
            raise InvalidAmount(amount)
        if src is dst:
            raise SameWallet(from_user)
        if amount > self._max:
            raise LimitExceeded(amount)
        fingerprint = (from_user, to_user, amount)
        with self._key_lock(idempotency_key):  # replays of one key are serialised
            done = self._keys.get(idempotency_key)
            if done is not None:
                if done[0] != fingerprint:
                    raise IdempotencyConflict(idempotency_key)
                return done[1]
            first, second = sorted((src, dst), key=lambda w: w.user)  # global lock order: no deadlock
            with first.lock, second.lock:
                if src.balance < amount:
                    raise InsufficientFunds(from_user)
                src.post(EntryType.TRANSFER_OUT, amount, -amount)
                dst.post(EntryType.TRANSFER_IN, amount, amount)
            txn = Transaction(f"T{next(self._ids)}", from_user, to_user, amount)
            self._keys[idempotency_key] = (fingerprint, txn)
            with self._txn_lock:
                self._txns[txn.id] = txn
            return txn

    def _move(self, src: Wallet, dst: Wallet, amount: int, out: EntryType, into: EntryType) -> None:
        first, second = sorted((src, dst), key=lambda w: w.user)  # global lock order: no deadlock
        with first.lock, second.lock:
            if src.balance < amount:
                raise InsufficientFunds(src.user)
            src.post(out, amount, -amount)
            dst.post(into, amount, amount)

    def reverse(self, transaction_id: str) -> Transaction:
        with self._txn_lock:  # also makes "reverse once" atomic
            original = self._txns.get(transaction_id)
            if original is None:
                raise UnknownTransaction(transaction_id)
            if transaction_id in self._reversed:
                raise AlreadyReversed(transaction_id)
            src, dst = self._wallet(original.to_user), self._wallet(original.from_user)
            self._move(src, dst, original.amount, EntryType.REVERSAL_OUT, EntryType.REVERSAL_IN)
            self._reversed.add(transaction_id)
            txn = Transaction(f"T{next(self._ids)}", src.user, dst.user, original.amount)
            self._txns[txn.id] = txn
            self._reversed.add(txn.id)  # a reversal is final
            return txn

    def balance(self, user: str) -> int:
        w = self._wallet(user)
        with w.lock:
            return w.balance

    def history(self, user: str) -> list[Entry]:
        w = self._wallet(user)
        with w.lock:
            return list(w.ledger)
