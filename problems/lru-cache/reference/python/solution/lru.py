from __future__ import annotations

import threading

from contract import Cache, CacheMiss


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: str = "", value: str = ""):
        self.key, self.value = key, value
        self.prev: _Node | None = None
        self.next: _Node | None = None


class LRUCache(Cache):
    """Hash map -> nodes of a doubly linked list (head = most recent). O(1) everything."""

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._map: dict[str, _Node] = {}
        self._head, self._tail = _Node(), _Node()  # sentinels
        self._head.next, self._tail.prev = self._tail, self._head
        self._lock = threading.Lock()

    def _unlink(self, n: _Node) -> None:
        n.prev.next, n.next.prev = n.next, n.prev

    def _push_front(self, n: _Node) -> None:
        n.prev, n.next = self._head, self._head.next
        self._head.next.prev = n
        self._head.next = n

    def get(self, key: str) -> str:
        with self._lock:
            n = self._map.get(key)
            if n is None:
                raise CacheMiss(key)
            self._unlink(n)
            self._push_front(n)
            return n.value

    def put(self, key: str, value: str) -> None:
        with self._lock:
            n = self._map.get(key)
            if n is not None:
                n.value = value
                self._unlink(n)
                self._push_front(n)
                return
            if len(self._map) >= self._capacity:
                lru = self._tail.prev
                self._unlink(lru)
                del self._map[lru.key]
            n = _Node(key, value)
            self._map[key] = n
            self._push_front(n)

    def delete(self, key: str) -> bool:
        with self._lock:
            n = self._map.pop(key, None)
            if n is None:
                return False
            self._unlink(n)
            return True

    def size(self) -> int:
        with self._lock:
            return len(self._map)

    def keys(self) -> list[str]:
        with self._lock:
            out, n = [], self._head.next
            while n is not self._tail:
                out.append(n.key)
                n = n.next
            return out
