from __future__ import annotations

from typing import Any, AsyncGenerator

import aiosqlite
from pydantic import BaseModel

from .base import BaseCollection, BaseDante


class Dante(BaseDante):
    async def get_connection(self) -> aiosqlite.Connection:
        if not self.conn:
            self.conn = await aiosqlite.connect(
                self.db_name,
                check_same_thread=self.check_same_thread,
            )

        return self.conn

    async def collection(
        self,
        name: str,
        model: BaseModel | None = None,
    ) -> "Collection":
        conn = await self.get_connection()
        await conn.execute(f"CREATE TABLE IF NOT EXISTS {name} (data TEXT)")
        await conn.commit()
        return Collection(name, self, model)

    async def commit(self):
        if self.conn:
            await self.conn.commit()

    async def _maybe_commit(self):
        if self.auto_commit and self.conn:
            await self.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None


class Collection(BaseCollection):
    """
    Asynchronous Dante collection.

    If the pydantic model class is specified, the data is automatically
    serialized/deserialized.

    :param name: Name of the collection
    :param db: Dante instance
    :param model: Pydantic model class (if using with Pydantic)
    """

    async def insert(self, data: dict[str, Any] | BaseModel):
        conn: aiosqlite.Connection = await self.db.get_connection()
        await conn.execute(
            f"INSERT INTO {self.name} (data) VALUES (?)", (self._to_json(data),)
        )
        await self.db._maybe_commit()

    async def find_many(
        _self,
        _limit: int | None = None,
        /,
        **kwargs: Any,
    ) -> list[dict[str, Any] | BaseModel]:
        query, values = _self._build_query(_limit, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        cursor = await conn.cursor()
        await cursor.execute(f"SELECT data FROM {_self.name}{query}", values)
        rows = await cursor.fetchall()

        return [_self._from_json(row[0]) for row in rows]

    async def find_one(_self, **kwargs: Any) -> dict | BaseModel | None:
        results = await _self.find_many(1, **kwargs)
        return results[0] if len(results) > 0 else None

    async def update(_self, _data: dict[str, Any] | BaseModel, /, **kwargs: Any) -> int:
        if not kwargs:
            raise ValueError("You must provide a filter to update")

        query, values = _self._build_query(None, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        cursor = await conn.execute(
            f"UPDATE {_self.name} SET data = ?{query}",
            (_self._to_json(_data), *values),
        )
        updated_rows = cursor.rowcount
        await _self.db._maybe_commit()
        return updated_rows

    async def set(_self, _fields: dict[str, Any], **kwargs: Any) -> int:
        if not _fields:
            raise ValueError("You must provide fields to set")

        if not kwargs:
            raise ValueError("You must provide a filter to update")

        set_clause, clause_values = _self._build_set_clause(**_fields)
        query, query_values = _self._build_query(None, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        cursor = await conn.execute(
            f"UPDATE {_self.name} {set_clause} {query}",
            *[clause_values + query_values],
        )
        updated_rows = cursor.rowcount
        await _self.db._maybe_commit()
        return updated_rows

    async def delete(_self, /, **kwargs: Any) -> int:
        if not kwargs:
            raise ValueError("You must provide a filter to delete")

        query, values = _self._build_query(None, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        cursor = await conn.execute(f"DELETE FROM {_self.name}{query}", values)
        deleted_rows = cursor.rowcount
        await _self.db._maybe_commit()
        return deleted_rows

    async def clear(self) -> int:
        conn: aiosqlite.Connection = await self.db.get_connection()
        cursor = await conn.execute(f"DELETE FROM {self.name}")
        deleted_rows = cursor.rowcount
        await self.db._maybe_commit()
        return deleted_rows

    async def __aiter__(self) -> AsyncGenerator[dict | BaseModel]:
        """
        Asynchronously iterate over the documents in the collection.
        """
        results = await self.find_many()
        for r in results:
            yield r
