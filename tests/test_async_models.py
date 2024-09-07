import pytest
from pydantic import BaseModel


class MyModel(BaseModel):
    a: int
    b: str = "foo"


@pytest.mark.asyncio
async def test_get_model_collection(db):
    coll = await db[MyModel]
    assert coll.model == MyModel
    assert coll.name == "MyModel"


@pytest.mark.asyncio
async def test_insert_find_one_model(db):
    coll = await db[MyModel]

    obj = MyModel(a=1)
    await coll.insert(obj)

    result = await coll.find_one(a=1)
    assert isinstance(result, MyModel)

    assert result.a == 1
    assert result.b == "foo"


@pytest.mark.asyncio
async def test_insert_find_many_model(db):
    coll = await db[MyModel]

    obj = MyModel(a=1)
    await coll.insert(obj)

    result = await coll.find_many(a=1)
    assert len(result) == 1
    assert isinstance(result[0], MyModel)

    assert result[0].a == 1
    assert result[0].b == "foo"


@pytest.mark.asyncio
async def test_update_model(db):
    coll = await db[MyModel]

    obj = MyModel(a=1)
    await coll.insert(obj)

    obj.b = "bar"
    await coll.update(obj, a=1)

    result = await coll.find_one(a=1)
    assert isinstance(result, MyModel)

    assert result.a == 1
    assert result.b == "bar"
