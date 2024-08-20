import pytest
from pydantic import BaseModel

from dante import AsyncDanteMixin


class MyModel(BaseModel):
    a: int
    b: str = "foo"


class MyDanteModel(AsyncDanteMixin, MyModel):
    pass


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
    await coll.update_many(obj, a=1)

    result = await coll.find_one(a=1)
    assert isinstance(result, MyModel)

    assert result.a == 1
    assert result.b == "bar"


@pytest.mark.asyncio
async def test_dante_mixin(db):
    """
    Test all behavior of async DanteMixin

    This is all in one big test to avoid concurrency
    issue stemming from overriding a singleton connection
    (within DanteMixin) with a fresh connection for each test.
    """
    AsyncDanteMixin.use_db(db)

    # Test object creation and single object retrieval
    obj = MyDanteModel(a=1)
    await obj.save()

    result = await MyDanteModel.find_one(a=1)
    assert isinstance(result, MyDanteModel)

    await MyDanteModel.clear()

    # Test object update and multiple object retrieval
    obj = MyDanteModel(a=1)
    await obj.save()

    obj.b = "bar"
    await obj.save(a=1)

    results = await MyDanteModel.find_many(a=1)
    assert len(results) == 1
    assert isinstance(results[0], MyDanteModel)

    assert results[0].a == 1
    assert results[0].b == "bar"

    await MyDanteModel.clear()

    # Test object deletion (single & many)
    obj = MyDanteModel(a=1)
    await obj.save()

    await obj.delete()

    result = await MyDanteModel.find_many()
    assert result == []

    await MyDanteModel.clear()

    obj = MyDanteModel(a=1, b="foo")
    await obj.save()

    obj = MyDanteModel(a=1, b="bar")
    await obj.save()

    await MyDanteModel.delete_many(a=1)

    result = await MyDanteModel.find_many()
    assert result == []
