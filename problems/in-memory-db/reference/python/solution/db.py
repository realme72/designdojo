from __future__ import annotations

import threading

from contract import Database, DuplicateTable, InvalidSchema, UnknownTable

from .table import Table


class MemoryDB(Database):
    def __init__(self):
        self._tables: dict[str, Table] = {}
        self._lock = threading.Lock()

    def _table(self, name: str) -> Table:
        with self._lock:
            t = self._tables.get(name)
        if t is None:
            raise UnknownTable(name)
        return t

    def create_table(self, name: str, columns: list[str], primary_key: str) -> None:
        if not columns or len(set(columns)) != len(columns) or primary_key not in columns:
            raise InvalidSchema(name)
        with self._lock:
            if name in self._tables:
                raise DuplicateTable(name)
            self._tables[name] = Table(columns, primary_key)

    def insert(self, table: str, row: dict[str, str]) -> None:
        t = self._table(table)
        with t.lock:
            t.insert(row)

    def select(self, table: str, where: dict[str, str], order_by: str, limit: int) -> list[dict[str, str]]:
        t = self._table(table)
        with t.lock:
            return t.select(where, order_by, limit)

    def update(self, table: str, where: dict[str, str], values: dict[str, str]) -> int:
        t = self._table(table)
        with t.lock:
            return t.update(where, values)

    def delete(self, table: str, where: dict[str, str]) -> int:
        t = self._table(table)
        with t.lock:
            return t.delete(where)

    def add_unique(self, table: str, column: str) -> None:
        t = self._table(table)
        with t.lock:
            t.add_unique(column)

    def create_index(self, table: str, column: str) -> None:
        t = self._table(table)
        with t.lock:
            t.check_columns([column])
            t.add_index(column)
