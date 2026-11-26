from __future__ import annotations

import threading
from collections import OrderedDict, defaultdict

from contract import Cache, CacheFull, CacheMiss


class LFUCache(Cache):
    """key -> (value, freq); freq -> OrderedDict of keys (oldest use first); tracked min freq."""

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._entries: dict[str, list] = {}  # key -> [value, freq]
        self._buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min = 0
        self._pinned: set[str] = set()
        self._lock = threading.Lock()

    def _touch(self, key: str) -> None:
        entry = self._entries[key]
        f = entry[1]
        del self._buckets[f][key]
        if not self._buckets[f]:
            del self._buckets[f]
            if self._min == f:
                self._min = f + 1
        entry[1] = f + 1
        self._buckets[f + 1][key] = None

    def get(self, key: str) -> str:
        with self._lock:
            if key not in self._entries:
                raise CacheMiss(key)
            self._touch(key)
            return self._entries[key][0]

    def put(self, key: str, value: str) -> None:
        with self._lock:
            if key in self._entries:
                self._entries[key][0] = value
                self._touch(key)
                return
            if len(self._entries) >= self._capacity:
                self._evict()
            self._entries[key] = [value, 1]
            self._buckets[1][key] = None
            self._min = 1

    def _evict(self) -> None:
        """Least frequent, then least recent, skipping pinned keys (fast path: min bucket)."""
        for f in [self._min] + sorted(k for k in self._buckets if k != self._min):
            victim = next((k for k in self._buckets.get(f, ()) if k not in self._pinned), None)
            if victim is not None:
                del self._buckets[f][victim]
                if not self._buckets[f]:
                    del self._buckets[f]
                del self._entries[victim]
                return
        raise CacheFull()

    def pin(self, key: str) -> None:
        with self._lock:
            if key not in self._entries:
                raise CacheMiss(key)
            self._pinned.add(key)

    def unpin(self, key: str) -> None:
        with self._lock:
            if key not in self._entries:
                raise CacheMiss(key)
            self._pinned.discard(key)

    def frequency(self, key: str) -> int:
        with self._lock:
            if key not in self._entries:
                raise CacheMiss(key)
            return self._entries[key][1]

    def size(self) -> int:
        with self._lock:
            return len(self._entries)
