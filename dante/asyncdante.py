from __future__ import annotations

import json
from typing import Iterable, TypeVar

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


DanteModel = TypeVar("DanteModel", bound="DanteMixin")


class DanteMixin:
    @classmethod
    def use_db(cls: DanteModel, db: str | Dante = Dante.MEMORY):
        if hasattr(cls, "_db"):
            return

        if isinstance(db, str):
            db = Dante(db)
        cls._db = db

    @classmethod
    async def close_db(cls: DanteModel):
        if hasattr(cls, "_db"):
            await cls._db.close()
            del cls._db

    @classmethod
    async def _get_collection(cls):
        coll = getattr(cls, "_collection", None)
        if coll:
            return coll
        coll = await cls._db.collection(cls.__name__, cls)
        cls._collection = coll
        return coll

    @classmethod
    async def find_many(cls: DanteModel, **kwargs) -> list[DanteModel]:
        coll = await cls._get_collection()
        return await coll.find_many(**kwargs)

    @classmethod
    async def find_one(cls: DanteModel, **kwargs) -> DanteModel | None:
        coll = await cls._get_collection()
        return await coll.find_one(**kwargs)

    async def save(self, **kwargs):
        coll = await self._get_collection()
        if kwargs:
            await coll.update_one(self, **kwargs)
        else:
            await coll.insert(self)

    async def delete(self):
        coll = await self._get_collection()
        data = json.loads(self.model_dump_json())
        await coll.delete_one(**data)

    @classmethod
    async def delete_many(self, **kwargs):
        coll = await self._get_collection()
        await coll.delete_many(**kwargs)

    @classmethod
    async def clear(cls: DanteModel):
        coll = await cls._get_collection()
        await coll.clear()
