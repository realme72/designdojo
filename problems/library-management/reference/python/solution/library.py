from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field

from contract import (Clock, DuplicateMember, InvalidAmount, InvalidCopies, Library, LoanLimitReached, Loan, NotAvailable,
                      OutstandingFines, UnknownBook, UnknownLoan, UnknownMember)

from .policy import DAY, FinePolicy


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    copies: int
    on_loan: int = 0


@dataclass
class Member:
    id: str
    owed: int = 0
    loans: dict[str, Loan] = field(default_factory=dict)  # insertion order = checkout order


class LendingLibrary(Library):
    def __init__(self, max_loans: int, loan_days: int, fines: FinePolicy, clock: Clock):
        self._max_loans = max_loans
        self._loan_seconds = loan_days * DAY
        self._fines = fines
        self._clock = clock
        self._books: dict[str, Book] = {}
        self._members: dict[str, Member] = {}
        self._active: dict[str, Loan] = {}
        self._ids = itertools.count(1)
        self._lock = threading.Lock()  # small system: one lock keeps book + member invariants together

    def _member(self, member_id: str) -> Member:
        m = self._members.get(member_id)
        if m is None:
            raise UnknownMember(member_id)
        return m

    def _book(self, isbn: str) -> Book:
        b = self._books.get(isbn)
        if b is None:
            raise UnknownBook(isbn)
        return b

    def add_book(self, isbn: str, title: str, author: str, copies: int) -> None:
        if copies < 1:
            raise InvalidCopies(copies)
        with self._lock:
            if isbn in self._books:
                self._books[isbn].copies += copies
            else:
                self._books[isbn] = Book(isbn, title, author, copies)

    def add_member(self, member_id: str) -> None:
        with self._lock:
            if member_id in self._members:
                raise DuplicateMember(member_id)
            self._members[member_id] = Member(member_id)

    def checkout(self, member_id: str, isbn: str) -> Loan:
        with self._lock:
            member = self._member(member_id)
            book = self._book(isbn)
            if member.owed > 0:
                raise OutstandingFines(member.owed)
            if len(member.loans) >= self._max_loans:
                raise LoanLimitReached(member_id)
            if book.on_loan >= book.copies:
                raise NotAvailable(isbn)
            loan = Loan(f"L{next(self._ids)}", member_id, isbn, self._clock.now() + self._loan_seconds)
            book.on_loan += 1
            member.loans[loan.id] = loan
            self._active[loan.id] = loan
            return loan

    def return_book(self, loan_id: str) -> int:
        with self._lock:
            loan = self._active.pop(loan_id, None)
            if loan is None:
                raise UnknownLoan(loan_id)
            member = self._members[loan.member_id]
            del member.loans[loan_id]
            self._books[loan.isbn].on_loan -= 1
            fine = self._fines.fine(loan.due_at, self._clock.now())
            member.owed += fine
            return fine

    def pay_fine(self, member_id: str, amount: int) -> int:
        with self._lock:
            member = self._member(member_id)
            if amount <= 0 or amount > member.owed:
                raise InvalidAmount(amount)
            member.owed -= amount
            return member.owed

    def fines(self, member_id: str) -> int:
        with self._lock:
            return self._member(member_id).owed

    def available(self, isbn: str) -> int:
        with self._lock:
            b = self._book(isbn)
            return b.copies - b.on_loan

    def loans(self, member_id: str) -> list[Loan]:
        with self._lock:
            return list(self._member(member_id).loans.values())

    def search(self, query: str) -> list[str]:
        q = query.lower()
        with self._lock:
            return sorted(b.isbn for b in self._books.values() if q in b.title.lower() or q in b.author.lower())
