from __future__ import annotations

import sqlite3
from typing import Any, Iterable

from pydantic import BaseModel

from .base import BaseCollection, BaseDante


class Dante(BaseDante):
    """
    Dante, a simple synchronous database wrapper for SQLite.

    :param db_name: Name of the database, defaults to in-memory database
    :param auto_commit: Whether to automatically commit transactions, defaults to True

    Usage:

    >>> from dante import Dante
    >>> db = Dante()
    >>> coll = db.collection("test")
    >>> coll.insert({"person": "Jane", "message": "Hello World!"})
    >>> result = coll.find_one(person="Jane")
    >>> result["message"] = "Goodbye World!"
    >>> coll.update_one(result, person="Jane")
    >>> coll.delete_one(person="Jane")
    """

    def get_connection(self) -> sqlite3.Connection:
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
    """
    Synchronous Dante collection.

    If the pydantic model class is specified, the data is automatically
    serialized/deserialized.

    :param name: Name of the collection
    :param db: Dante instance
    :param model: Pydantic model class (if using with Pydantic)
    """

    def insert(self, data: dict[str, Any] | BaseModel):
        cursor = self.conn.cursor()
        cursor.execute(
            f"INSERT INTO {self.name} (data) VALUES (?)", (self._to_json(data),)
        )
        self.db._maybe_commit()

    def find_many(
        _self,
        _limit: int | None = None,
        /,
        **kwargs: Any,
    ) -> list[dict | BaseModel]:
        query, values = _self._build_query(_limit, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(f"SELECT data FROM {_self.name}{query}", values)
        rows = cursor.fetchall()

        return [_self._from_json(row[0]) for row in rows]

    def find_one(_self, **kwargs: Any) -> dict | BaseModel | None:
        results = _self.find_many(1, **kwargs)
        return results[0] if len(results) > 0 else None

    def update(_self, _data: dict[str, Any] | BaseModel, /, **kwargs: Any):
        if not kwargs:
            raise ValueError("You must provide a filter to update")

        query, values = _self._build_query(None, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(
            f"UPDATE {_self.name} SET data = ? {query}",
            (_self._to_json(_data), *values),
        )
        _self.db._maybe_commit()

    def set(_self, _fields: dict[str, Any], **kwargs: Any):
        if not _fields:
            raise ValueError("You must provide fields to set")

        if not kwargs:
            raise ValueError("You must provide a filter to update")

        set_clause, clause_values = _self._build_set_clause(**_fields)
        query, query_values = _self._build_query(None, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(
            f"UPDATE {_self.name} {set_clause} {query}",
            *[clause_values + query_values],
        )
        _self.db._maybe_commit()

    def delete(_self, /, **kwargs: Any):
        if not kwargs:
            raise ValueError("You must provide a filter to delete")

        query, values = _self._build_query(None, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(f"DELETE FROM {_self.name}{query}", values)
        _self.db._maybe_commit()

    def clear(self):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.name}")
        self.db._maybe_commit()

    def __iter__(self) -> Iterable[dict[str, Any] | BaseModel]:
        """
        Iterate over the documents in the collection.
        """
        return iter(self.find_many())
