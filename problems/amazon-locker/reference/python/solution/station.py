from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass

from contract import (Clock, DuplicateCode, DuplicateLocker, DuplicatePackage, Expired, InvalidCode, LockerStation,
                      NoLockerAvailable, Size)

RANK = {s: i for i, s in enumerate(Size)}  # enum order is size order


@dataclass
class Locker:
    id: str
    size: Size
    package: str | None = None


@dataclass
class Parcel:
    id: str
    locker: Locker
    code: str
    deposited_at: int


class AssignmentPolicy(ABC):
    @abstractmethod
    def choose(self, free: list[Locker], size: Size) -> Locker | None: ...


class SmallestFit(AssignmentPolicy):
    def choose(self, free, size):
        fits = [l for l in free if RANK[l.size] >= RANK[size]]
        return min(fits, key=lambda l: (RANK[l.size], l.id), default=None)


class Station(LockerStation):
    def __init__(self, hold_seconds: int, clock: Clock, policy: AssignmentPolicy):
        self._hold = hold_seconds
        self._clock = clock
        self._policy = policy
        self._lockers: dict[str, Locker] = {}
        self._by_code: dict[str, Parcel] = {}
        self._packages: set[str] = set()
        self._lock = threading.Lock()

    def add_locker(self, locker_id: str, size: Size) -> None:
        with self._lock:
            if locker_id in self._lockers:
                raise DuplicateLocker(locker_id)
            self._lockers[locker_id] = Locker(locker_id, size)

    def deposit(self, package_id: str, size: Size, code: str) -> str:
        with self._lock:
            if package_id in self._packages:
                raise DuplicatePackage(package_id)
            if code in self._by_code:
                raise DuplicateCode(code)
            locker = self._policy.choose([l for l in self._lockers.values() if l.package is None], size)
            if locker is None:
                raise NoLockerAvailable(size.name)
            locker.package = package_id
            self._by_code[code] = Parcel(package_id, locker, code, self._clock.now())
            self._packages.add(package_id)
            return locker.id

    def _expired(self, p: Parcel) -> bool:
        return self._clock.now() >= p.deposited_at + self._hold

    def _remove(self, p: Parcel) -> None:
        del self._by_code[p.code]
        self._packages.discard(p.id)
        p.locker.package = None

    def pickup(self, code: str) -> str:
        with self._lock:
            p = self._by_code.get(code)
            if p is None:
                raise InvalidCode()
            if self._expired(p):
                raise Expired(p.id)
            self._remove(p)
            return p.id

    def reclaim_expired(self) -> list[str]:
        with self._lock:
            expired = [p for p in self._by_code.values() if self._expired(p)]
            for p in expired:
                self._remove(p)
            return sorted(p.id for p in expired)

    def free_count(self, size: Size) -> int:
        with self._lock:
            return sum(1 for l in self._lockers.values() if l.size is size and l.package is None)
