from __future__ import annotations

import sqlite3
from typing import Iterable

from pydantic import BaseModel

from .base import BaseCollection, BaseDante


class Dante(BaseDante):
    def get_connection(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def collection(self, name: str, model: BaseModel | None = None) -> "Collection":
        conn = self.get_connection()
        conn.execute(f"CREATE TABLE IF NOT EXISTS {name} (data TEXT)")
        conn.commit()
        return Collection(name, self, model)

    def commit(self):
        if self.conn:
            self.conn.commit()

    def _maybe_commit(self):
        if self.auto_commit and self.conn:
            self.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


class Collection(BaseCollection):
    def insert(self, data: dict | BaseModel):
        cursor = self.conn.cursor()
        cursor.execute(
            f"INSERT INTO {self.name} (data) VALUES (?)", (self._to_json(data),)
        )
        self.db._maybe_commit()

    def find_many(_self, _limit=None, /, **kwargs) -> list[dict | BaseModel]:
        query, values = _self._build_query(_limit, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(f"SELECT data FROM {_self.name}{query}", values)
        rows = cursor.fetchall()

        return [_self._from_json(row[0]) for row in rows]

    def find_one(_self, **kwargs) -> dict | BaseModel | None:
        results = _self.find_many(1, **kwargs)
        return results[0] if len(results) > 0 else None

    def update_many(_self, _data: dict | BaseModel, _limit=None, /, **kwargs):
        if not kwargs:
            raise ValueError("You must provide a filter to update")

        query, values = _self._build_query(_limit, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(
            f"UPDATE {_self.name} SET data = ? {query}",
            (_self._to_json(_data), *values),
        )
        _self.db._maybe_commit()

    def update_one(_self, _data: dict | BaseModel, /, **kwargs):
        _self.update_many(_data, None, **kwargs)

    def delete_many(_self, _limit=None, /, **kwargs):
        if not kwargs:
            raise ValueError("You must provide a filter to delete")

        query, values = _self._build_query(_limit, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(f"DELETE FROM {_self.name}{query}", values)
        _self.db._maybe_commit()

    def delete_one(_self, /, **kwargs):
        _self.delete_many(None, **kwargs)

    def clear(self):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.name}")
        self.db._maybe_commit()

    def __iter__(self) -> Iterable[dict | BaseModel]:
        return iter(self.find_many())
