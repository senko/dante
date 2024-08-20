from asyncio import gather
from datetime import datetime
from time import time

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
async def test_update_one(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    await coll.update_many({"a": 1, "b": 3}, a=1)
    result = await coll.find_one(a=1)
    assert result["b"] == 3


@pytest.mark.asyncio
async def test_update_many(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    await coll.update_many({"a": 1, "b": 3}, a=1)
    result = await coll.find_one(a=1)
    assert result["b"] == 3


@pytest.mark.asyncio
async def test_delete_one(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    await coll.delete_many(a=1)
    result = await coll.find_one(a=1)
    assert result is None


@pytest.mark.asyncio
async def test_delete_many(db):
    coll = await db["test"]

    await gather(
        coll.insert({"a": 1, "b": 2}),
        coll.insert({"a": 1, "b": 3}),
    )
    await coll.delete_many(a=1)
    result = await coll.find_many(a=1)
    assert result == []


@pytest.mark.asyncio
async def test_clear(db):
    coll = await db["test"]

    await coll.insert({"a": 1, "b": 2})
    await coll.clear()
    result = await coll.find_many()
    assert result == []


@pytest.mark.asyncio
async def test_insert_performance(tmp_path):
    db_path = tmp_path / "test.db"
    db = AsyncDante(db_path, auto_commit=False)

    coll = await db["test"]
    t0 = time()
    coros = []
    for i in range(100):
        coros.append(coll.insert({"a": i, "b": i + 1}))
    await gather(*coros)
    await db.commit()
    t1 = time()
    dt = t1 - t0
    assert dt < 0.05
    await db.close()


@pytest.mark.asyncio
async def test_update_performance(tmp_path):
    db_path = tmp_path / "test.db"
    db = AsyncDante(db_path, auto_commit=False)

    coll = await db["test"]
    coros = []
    for i in range(100):
        coros.append(coll.insert({"a": i, "b": i + 1}))

    await gather(*coros)
    await db.commit()

    t0 = time()
    coros = []
    for i in range(100):
        coros.append(coll.update_one({"a": i, "b": 2 * i + 1}, a=i))
    await gather(*coros)
    await db.commit()
    t1 = time()
    dt = t1 - t0
    assert dt < 0.1
    await db.close()
