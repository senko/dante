import pytest
from pydantic import BaseModel

from dante import Dante


class MyModel(BaseModel):
    a: int
    b: str = "foo"


def test_get_model_collection():
    db = Dante()
    coll = db[MyModel]
    assert coll.model == MyModel
    assert coll.name == "MyModel"


def test_insert_find_one_model():
    db = Dante()
    coll = db[MyModel]

    obj = MyModel(a=1)
    coll.insert(obj)

    result = coll.find_one(a=1)
    assert isinstance(result, MyModel)

    assert result.a == 1
    assert result.b == "foo"


def test_insert_find_many_model():
    db = Dante()
    coll = db[MyModel]

    obj = MyModel(a=1)
    coll.insert(obj)

    result = coll.find_many(a=1)
    assert len(result) == 1
    assert isinstance(result[0], MyModel)

    assert result[0].a == 1
    assert result[0].b == "foo"


def test_update_model():
    db = Dante()
    coll = db[MyModel]

    obj = MyModel(a=1)
    coll.insert(obj)

    obj.b = "bar"
    coll.update(obj, a=1)

    result = coll.find_one(a=1)
    assert isinstance(result, MyModel)

    assert result.a == 1
    assert result.b == "bar"


def test_update_without_filter_fails():
    db = Dante()
    coll = db[MyModel]

    obj = MyModel(a=1)

    with pytest.raises(ValueError):
        coll.update(obj)


def test_delete_without_filter_fails():
    db = Dante()
    coll = db[MyModel]

    with pytest.raises(ValueError):
        coll.delete()
