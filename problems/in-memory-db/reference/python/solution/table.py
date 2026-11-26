from __future__ import annotations

import threading
from collections import defaultdict

from contract import DuplicateKey, InvalidQuery, InvalidRow, InvalidSchema, UnknownColumn


class Table:
    def __init__(self, columns: list[str], pk: str):
        self.columns, self.pk = list(columns), pk
        self.rows: dict[str, dict[str, str]] = {}
        self.indexes: dict[str, defaultdict[str, set[str]]] = {}
        self.unique: set[str] = set()
        self.lock = threading.Lock()

    # ---- schema checks ----
    def check_columns(self, names) -> None:
        unknown = [n for n in names if n not in self.columns]
        if unknown:
            raise UnknownColumn(unknown)

    # ---- constraints ----
    def add_unique(self, column: str) -> None:
        self.check_columns([column])
        values = [r[column] for r in self.rows.values()]
        if len(values) != len(set(values)):
            raise InvalidSchema(f"{column} already has duplicates")
        self.unique.add(column)

    def _check_unique(self, rows) -> None:
        for col in self.unique:
            values = [r[col] for r in rows]
            if len(values) != len(set(values)):
                raise DuplicateKey(col)

    # ---- index maintenance ----
    def _index_add(self, key: str, row: dict[str, str]) -> None:
        for col, idx in self.indexes.items():
            idx[row[col]].add(key)

    def _index_remove(self, key: str, row: dict[str, str]) -> None:
        for col, idx in self.indexes.items():
            idx[row[col]].discard(key)

    def add_index(self, column: str) -> None:
        idx: defaultdict[str, set[str]] = defaultdict(set)
        for k, row in self.rows.items():
            idx[row[column]].add(k)
        self.indexes[column] = idx

    # ---- query pipeline: candidates -> filter -> sort -> limit ----
    def matching_keys(self, where: dict[str, str]) -> list[str]:
        self.check_columns(where)
        indexed = next((c for c in where if c in self.indexes or c == self.pk), None)
        if indexed == self.pk:
            candidates = [where[self.pk]] if where[self.pk] in self.rows else []
        elif indexed:
            candidates = list(self.indexes[indexed].get(where[indexed], ()))
        else:
            candidates = list(self.rows)
        return [k for k in candidates if all(self.rows[k][c] == v for c, v in where.items())]

    def select(self, where, order_by: str, limit: int) -> list[dict[str, str]]:
        if limit < 0:
            raise InvalidQuery(limit)
        if order_by:
            self.check_columns([order_by])
        keys = self.matching_keys(where)
        col = order_by or self.pk
        keys.sort(key=lambda k: (self.rows[k][col], k))
        if limit:
            keys = keys[:limit]
        return [dict(self.rows[k]) for k in keys]

    # ---- writes ----
    def insert(self, row: dict[str, str]) -> None:
        if set(row) != set(self.columns):
            raise InvalidRow(sorted(row))
        key = row[self.pk]
        if key in self.rows:
            raise DuplicateKey(key)
        self._check_unique([*self.rows.values(), row])
        self.rows[key] = dict(row)
        self._index_add(key, self.rows[key])

    def update(self, where, values) -> int:
        self.check_columns(values)
        keys = self.matching_keys(where)
        new_rows = {k: {**self.rows[k], **values} for k in keys}
        if self.pk in values:  # validate key uniqueness before touching anything
            new_keys = [r[self.pk] for r in new_rows.values()]
            untouched = set(self.rows) - set(keys)
            if len(set(new_keys)) != len(new_keys) or any(k in untouched for k in new_keys):
                raise DuplicateKey(values[self.pk])
        self._check_unique([r for k, r in self.rows.items() if k not in new_rows] + list(new_rows.values()))
        for k in keys:
            self._index_remove(k, self.rows.pop(k))
        for row in new_rows.values():
            self.rows[row[self.pk]] = row
            self._index_add(row[self.pk], row)
        return len(keys)

    def delete(self, where) -> int:
        keys = self.matching_keys(where)
        for k in keys:
            self._index_remove(k, self.rows.pop(k))
        return len(keys)
