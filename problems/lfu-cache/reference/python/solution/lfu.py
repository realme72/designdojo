from __future__ import annotations

import threading
from collections import OrderedDict, defaultdict

from contract import Cache, CacheMiss


class LFUCache(Cache):
    """key -> (value, freq); freq -> OrderedDict of keys (oldest use first); tracked min freq."""

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._entries: dict[str, list] = {}  # key -> [value, freq]
        self._buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min = 0
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
                victim, _ = self._buckets[self._min].popitem(last=False)
                if not self._buckets[self._min]:
                    del self._buckets[self._min]
                del self._entries[victim]
            self._entries[key] = [value, 1]
            self._buckets[1][key] = None
            self._min = 1

    def frequency(self, key: str) -> int:
        with self._lock:
            if key not in self._entries:
                raise CacheMiss(key)
            return self._entries[key][1]

    def size(self) -> int:
        with self._lock:
            return len(self._entries)
