from pydantic import BaseModel

from dante import Dante, DanteMixin


class MyModel(BaseModel):
    a: int
    b: str = "foo"


class MyDanteModel(DanteMixin, MyModel):
    pass


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
    coll.update_many(obj, a=1)

    result = coll.find_one(a=1)
    assert isinstance(result, MyModel)

    assert result.a == 1
    assert result.b == "bar"


def test_dante_model_insert():
    DanteMixin.use_db()
    MyDanteModel.clear()

    obj = MyDanteModel(a=1)
    obj.save()

    result = MyDanteModel.find_one(a=1)
    assert isinstance(result, MyDanteModel)


def test_dante_model_update():
    DanteMixin.use_db()
    MyDanteModel.clear()

    obj = MyDanteModel(a=1)
    obj.save()

    obj.b = "bar"
    obj.save(a=1)

    results = MyDanteModel.find_many(a=1)
    assert len(results) == 1
    assert isinstance(results[0], MyDanteModel)

    assert results[0].a == 1
    assert results[0].b == "bar"


def test_dante_model_delete():
    DanteMixin.use_db()
    MyDanteModel.clear()

    obj = MyDanteModel(a=1)
    obj.save()

    obj.delete()

    result = MyDanteModel.find_many()
    assert result == []


def test_dante_model_delete_many():
    DanteMixin.use_db()
    MyDanteModel.clear()

    obj = MyDanteModel(a=1, b="foo")
    obj.save()

    obj = MyDanteModel(a=1, b="bar")
    obj.save()

    MyDanteModel.delete_many(a=1)

    result = MyDanteModel.find_many()
    assert result == []
