from __future__ import annotations

from collections import Counter

from contract import InvalidValue, KeyNotFound, KeyValueStore, NoTransaction

_MISSING = object()


class _Data:
    """Applies writes and keeps the value -> count index in step."""

    def __init__(self):
        self.values: dict[str, str] = {}
        self.counts: Counter[str] = Counter()

    def write(self, key: str, value) -> None:
        old = self.values.get(key, _MISSING)
        if old is not _MISSING:
            self.counts[old] -= 1
        if value is _MISSING:
            self.values.pop(key, None)
        else:
            self.values[key] = value
            self.counts[value] += 1


class TransactionalStore(KeyValueStore):
    """Stack of undo logs: each level remembers a key's value before its first write there."""

    def __init__(self):
        self._data = _Data()
        self._undo: list[dict[str, object]] = []

    def _write(self, key: str, value) -> None:
        if self._undo and key not in self._undo[-1]:
            self._undo[-1][key] = self._data.values.get(key, _MISSING)
        self._data.write(key, value)

    def set(self, key: str, value: str) -> None:
        self._write(key, value)

    def get(self, key: str) -> str:
        if key not in self._data.values:
            raise KeyNotFound(key)
        return self._data.values[key]

    def delete(self, key: str) -> bool:
        if key not in self._data.values:
            return False
        self._write(key, _MISSING)
        return True

    def incr(self, key: str, by: int) -> int:
        current = self._data.values.get(key, "0")
        try:
            n = int(current) + by
        except ValueError:
            raise InvalidValue(current) from None
        self._write(key, str(n))
        return n

    def count(self, value: str) -> int:
        return self._data.counts[value]

    def keys(self, prefix: str) -> list[str]:
        return sorted(k for k in self._data.values if k.startswith(prefix))

    def begin(self) -> None:
        self._undo.append({})

    def rollback(self) -> None:
        if not self._undo:
            raise NoTransaction()
        for key, old in self._undo.pop().items():
            self._data.write(key, old)

    def commit(self) -> None:
        if not self._undo:
            raise NoTransaction()
        inner = self._undo.pop()
        if self._undo:  # parent keeps the oldest pre-image of each key
            parent = self._undo[-1]
            for key, old in inner.items():
                parent.setdefault(key, old)
