from asyncio import gather
from datetime import datetime

import pytest

from dante import AsyncDante


@pytest.mark.asyncio
async def test_create_dante_on_disk(tmp_path):
    db_path = tmp_path / "test.db"
    db = AsyncDante(db_path)
    assert db is not None

    assert not db_path.exists()

    coll = await db["test"]
    assert coll is not None
    assert db_path.exists()
    await db.close()


@pytest.mark.asyncio
async def test_create_collection(db):
    coll = await db["test"]
    assert coll is not None
    q = await db.conn.execute("select name from sqlite_master where type = 'table'")
    x = await q.fetchone()
    assert x == ("test",)


@pytest.mark.asyncio
async def test_insert_find_one(db):
    coll = await db["test"]

    data = {"a": 1, "b": 2}
    await coll.insert(data)
    result = await coll.find_one(a=1, b=2)
    assert result == data


@pytest.mark.asyncio
async def test_insert_find_many(db):
    coll = await db["test"]

    obj1 = {"a": 1, "b": 2, "c": 3}
    obj2 = {"a": 1, "e": 4, "f": 5}
    await gather(
        coll.insert(obj1),
        coll.insert(obj2),
    )
    result = await coll.find_many(a=1)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_insert_datetime(db):
    coll = await db["test"]

    data = {"a": 1, "b": datetime.now()}
    await coll.insert(data)
    result = await coll.find_one(a=1)
    assert datetime.fromisoformat(result["b"]) == data["b"]


@pytest.mark.asyncio
async def test_find_none(db):
    coll = await db["test"]

    result = await coll.find_one(a=1)
    assert result is None


@pytest.mark.asyncio
async def test_iteration(db):
    coll = await db["test"]

    await coll.insert({"a": 1})

    count = 0
    async for data in coll:
        count += 1
        assert data["a"] == 1

    assert count == 1


@pytest.mark.asyncio
async def test_update(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    n = await coll.update({"a": 1, "b": 3}, a=1)
    assert n == 1
    result = await coll.find_one(a=1)
    assert result["b"] == 3


@pytest.mark.asyncio
async def test_update_without_filter_fails(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    with pytest.raises(ValueError):
        await coll.update({})


@pytest.mark.asyncio
async def test_set(db):
    coll = await db["test"]
    await coll.insert({"a": 1, "b": 2})
    n = await coll.set({"b": 3}, a=1)
    assert n == 1
    result = await coll.find_one(a=1)
    assert result["b"] == 3


@pytest.mark.asyncio
async def test_set_without_fields_fails(db):
    coll = await db["test"]
    with pytest.raises(ValueError):
        await coll.set({}, a=1)


@pytest.mark.asyncio
async def test_set_without_filter_fails(db):
    coll = await db["test"]
    with pytest.raises(ValueError):
        await coll.set({"a": 1})


@pytest.mark.asyncio
async def test_delete(db):
    coll = await db["test"]

    await gather(
        coll.insert({"a": 1, "b": 2}),
        coll.insert({"a": 1, "b": 3}),
    )
    n = await coll.delete(a=1)
    assert n == 2
    result = await coll.find_many(a=1)
    assert result == []


@pytest.mark.asyncio
async def test_delete_without_filter_fails(db):
    coll = await db["test"]

    with pytest.raises(ValueError):
        await coll.delete()


@pytest.mark.asyncio
async def test_clear(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    n = await coll.clear()
    assert n == 1
    result = await coll.find_many()
    assert result == []
