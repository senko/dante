from __future__ import annotations

from typing import Iterable

import aiosqlite
from pydantic import BaseModel

from .base import BaseCollection, BaseDante


class Dante(BaseDante):
    async def get_connection(self) -> aiosqlite.Connection:
        if not self.conn:
            self.conn = await aiosqlite.connect(self.db_name)
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
            await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None


class Collection(BaseCollection):
    async def insert(self, data: dict | BaseModel):
        conn: aiosqlite.Connection = await self.db.get_connection()
        await conn.execute(
            f"INSERT INTO {self.name} (data) VALUES (?)", (self._to_json(data),)
        )
        await self.db._maybe_commit()

    async def find_many(_self, _limit=None, /, **kwargs) -> list[dict | BaseModel]:
        query, values = _self._build_query(_limit, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        cursor = await conn.cursor()
        await cursor.execute(f"SELECT data FROM {_self.name}{query}", values)
        rows = await cursor.fetchall()

        return [_self._from_json(row[0]) for row in rows]

    async def find_one(_self, **kwargs) -> dict | BaseModel | None:
        results = await _self.find_many(1, **kwargs)
        return results[0] if len(results) > 0 else None

    async def update_many(_self, _data: dict | BaseModel, _limit=None, /, **kwargs):
        if not kwargs:
            raise ValueError("You must provide a filter to update")

        query, values = _self._build_query(_limit, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        await conn.execute(
            f"UPDATE {_self.name} SET data = ? {query}",
            (_self._to_json(_data), *values),
        )
        await _self.db._maybe_commit()

    async def update_one(_self, _data: dict | BaseModel, /, **kwargs):
        await _self.update_many(_data, None, **kwargs)

    async def delete_many(_self, _limit=None, /, **kwargs):
        if not kwargs:
            raise ValueError("You must provide a filter to delete")

        query, values = _self._build_query(_limit, **kwargs)

        conn: aiosqlite.Connection = await _self.db.get_connection()
        await conn.execute(f"DELETE FROM {_self.name}{query}", values)
        await _self.db._maybe_commit()

    async def delete_one(_self, /, **kwargs):
        await _self.delete_many(None, **kwargs)

    async def clear(self):
        conn: aiosqlite.Connection = await self.db.get_connection()
        await conn.execute(f"DELETE FROM {self.name}")
        await self.db._maybe_commit()

    def __aiter__(self) -> Iterable[dict | BaseModel]:
        return iter(self.find_many())
