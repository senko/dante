from datetime import datetime
from time import time

from dante.sync import Dante


def test_create_dante_on_disk(tmp_path):
    db_path = tmp_path / "test.db"
    db = Dante(db_path)
    assert db is not None
    _ = db["test"]
    assert db_path.exists()


def test_create_collection():
    db = Dante()
    coll = db["test"]
    assert coll is not None
    x = (
        db.conn.cursor()
        .execute("select name from sqlite_master where type = 'table'")
        .fetchone()
    )
    assert x == ("test",)


def test_insert_find_one():
    db = Dante()
    coll = db["test"]

    data = {"a": 1, "b": 2}
    coll.insert(data)
    result = coll.find_one(a=1, b=2)
    assert result == data


def test_insert_find_many():
    db = Dante()
    coll = db["test"]

    obj1 = {"a": 1, "b": 2, "c": 3}
    obj2 = {"a": 1, "e": 4, "f": 5}
    coll.insert(obj1)
    coll.insert(obj2)
    result = coll.find_many(a=1)
    assert len(result) == 2


def test_insert_datetime():
    db = Dante()
    coll = db["test"]

    data = {"a": 1, "b": datetime.now()}
    coll.insert(data)
    result = coll.find_one(a=1)
    assert datetime.fromisoformat(result["b"]) == data["b"]


def test_find_none():
    db = Dante()
    coll = db["test"]

    result = coll.find_one(a=1)
    assert result is None


def test_update_one():
    db = Dante()
    coll = db["test"]

    coll.insert({"a": 1, "b": 2})
    coll.update_many({"a": 1, "b": 3}, a=1)
    result = coll.find_one(a=1)
    assert result["b"] == 3


def test_update_many():
    db = Dante()
    coll = db["test"]

    coll.insert({"a": 1, "b": 2})
    coll.update_many({"a": 1, "b": 3}, a=1)
    result = coll.find_one(a=1)
    assert result["b"] == 3


def test_delete_one():
    db = Dante()
    coll = db["test"]

    coll.insert({"a": 1, "b": 2})
    coll.delete_many(a=1)
    result = coll.find_one(a=1)
    assert result is None


def test_delete_many():
    db = Dante()
    coll = db["test"]

    coll.insert({"a": 1, "b": 2})
    coll.insert({"a": 1, "b": 3})
    coll.delete_many(a=1)
    result = coll.find_many(a=1)
    assert result == []


def test_clear():
    db = Dante()
    coll = db["test"]

    coll.insert({"a": 1, "b": 2})
    coll.clear()
    result = coll.find_many()
    assert result == []


def test_insert_performance(tmp_path):
    db_path = tmp_path / "test.db"
    db = Dante(db_path, auto_commit=False)

    coll = db["test"]
    t0 = time()
    for i in range(100):
        coll.insert({"a": i, "b": i + 1})
    db.commit()
    t1 = time()
    dt = t1 - t0
    assert dt < 0.05


def test_update_performance(tmp_path):
    db_path = tmp_path / "test.db"
    db = Dante(db_path, auto_commit=False)

    coll = db["test"]
    for i in range(100):
        coll.insert({"a": i, "b": i + 1})

    db.commit()
    t0 = time()
    for i in range(100):
        coll.update_one({"a": i, "b": 2 * i + 1}, a=i)
    db.commit()
    t1 = time()
    dt = t1 - t0
    assert dt < 0.1
