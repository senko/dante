from __future__ import annotations

import sqlite3
from typing import Any, Iterable


from .base import BaseCollection, BaseDante, TModel


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
            self.conn = sqlite3.connect(
                self.db_name,
                check_same_thread=self.check_same_thread,
            )
        return self.conn

    def collection(self, name: str, model: TModel | None = None) -> Collection:
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

    @property
    def conn(self) -> sqlite3.Connection:
        return self.db.get_connection()

    def insert(self, data: dict[str, Any] | TModel):
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
    ) -> list[dict | TModel]:
        query, values = _self._build_query(_limit, **kwargs)

        cursor = _self.conn.execute(f"SELECT data FROM {_self.name}{query}", values)
        rows = cursor.fetchall()

        return [_self._from_json(row[0]) for row in rows]

    def find_one(_self, **kwargs: Any) -> dict | TModel | None:
        results = _self.find_many(1, **kwargs)
        return results[0] if len(results) > 0 else None

    def update(_self, _data: dict[str, Any] | TModel, /, **kwargs: Any) -> int:
        if not kwargs:
            raise ValueError("You must provide a filter to update")

        query, values = _self._build_query(None, **kwargs)

        cursor = _self.conn.cursor()
        cursor.execute(
            f"UPDATE {_self.name} SET data = ? {query}",
            (_self._to_json(_data), *values),
        )
        updated_rows = cursor.rowcount
        _self.db._maybe_commit()
        return updated_rows

    def set(_self, _fields: dict[str, Any], **kwargs: Any) -> int:
        if not _fields:
            raise ValueError("You must provide fields to set")

        if not kwargs:
            raise ValueError("You must provide a filter to update")

        set_clause, clause_values = _self._build_set_clause(**_fields)
        query, query_values = _self._build_query(None, **kwargs)

        cursor = _self.conn.execute(
            f"UPDATE {_self.name} {set_clause} {query}",
            *[clause_values + query_values],
        )
        updated_rows = cursor.rowcount
        _self.db._maybe_commit()
        return updated_rows

    def delete(_self, /, **kwargs: Any) -> int:
        if not kwargs:
            raise ValueError("You must provide a filter to delete")

        query, values = _self._build_query(None, **kwargs)

        cursor = _self.conn.execute(f"DELETE FROM {_self.name}{query}", values)
        deleted_rows = cursor.rowcount
        _self.db._maybe_commit()
        return deleted_rows

    def clear(self) -> int:
        cursor = self.conn.execute(f"DELETE FROM {self.name}")
        deleted_rows = cursor.rowcount
        self.db._maybe_commit()
        return deleted_rows

    def __iter__(self) -> Iterable[dict[str, Any] | TModel]:
        """
        Iterate over the documents in the collection.
        """
        return iter(self.find_many())
