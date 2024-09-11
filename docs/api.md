# API Reference

Dante supports both sync and async usage. The API is identical for both modes,
with the exception of the `AsyncDante` class and the `await` keyword for
async operations.

Note: Dante may export additional API elements that are not documented here. These are considered internal and may change without notice.

## Quick Reference

- [Dante](#dante) - represents a database
  - [Dante()](#constructor) - open the database
  - [Dante.commit()](#commit) - commit changes (use if `auto_commit=False`)
  - [Dante.close()](#close) - close the database
- [Collection](#collection) - represents a collection of documents in a database
  - [Plain Python objects](#plain-python-objects) - use with Python dictionaries
  - [Pydantic models](#pydantic-models) - use with Pydantic model
    - [Collection.insert()](#insert) - insert a document
    - [Collection.find_one()](#find) - find a document
    - [Collection.find_many()](#find) - find multiple documents
    - [Collection.update()](#update) - update matching document(s)
    - [Collection.set()](#set) - update specific fields in matching document(s)
    - [Collection.delete()](#delete) - delete matching document(s)
    - [Collection.clear()](#clear) - delete all documents


## `Dante`

The main classes for sync usage. A Dante instance represents a database.

### Constructor

`Dante(db_name: str, auto_commit: bool, check_same_thread: bool)` opens the database at the specified path, creating it if it doesn't already exist.

If the `auto_commit` parameter is `True` (the default), the database will automatically commit changes after each operation. Otherwise, you need to call `commit()` manually.

If the `check_same_thread` parameter is `True` (the default), the database will only be accessible from the thread that created it (see [SQLite docs](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect) for more info). If you want to access the same database connection from multiple threads, set this parameter to `False`. This is useful for frameworks like FastAPI that run in multiple threads.

If you omit the database name, Dante will create an in-memory database that will be lost when the program exits.

Sync example:

```python
from dante import Dante

db = Dante("mydatabase.db")
```

Async example:

```python
from dante import AsyncDante as Dante

db = Dante("mydatabase.db")
```

### Commit

Commits the changes to the database. If you set `auto_commit=False` in the constructor, you need to call this method manually.

Sync:

```python
db.commit()
```

Async:

```python
await db.commit()
```


### Close

Closes the database connection. You only need to call this method if you want to close the database before the program exits, as it will be closed automatically at exit.

Sync:

```python
db.close()
```

Async:

```python
await db.close()
```

## `Collection`

A collection of documents in the database, corresponding to a database table.
Each documents is a Python dict or a Pydantic model.

To get a collection from the database, index it with the collection name or
the Pydantic model class.

### Plain Python objects

When the collection is named using a string, it will work with (accept and
return) Python dictionaries, which may be nested and contain any
JSON-serializable data types and date/datetime objects.

Sync:

```python
collection = db["mycollection"]
```

Async:

```python
collection = await db["mycollection"]
```

### Pydantic models

When the collection is named using a Pydantic model class, it will work with
instances of that model. Serialization/deserializion is handled by Pydantic.

Sync:

```python
collection = db[MyPydanticModel]
```

Async:

```python
collection = await db[MyPydanticModel]
```

### Insert

Inserts a document into the collection.

Sync with Python dict:

```python
collection.insert({"name": "Dante", "text": "Hello world!"})
```

Sync with Pydantic model:

```python
obj = MyPydanticModel(name="Dante", text="Hello world!")
collection.insert(obj)
```

Async with Python dict:

```python
await collection.insert({"name": "Dante", "text": "Hello world!"})
```

Async with Pydantic model:

```python
obj = MyPydanticModel(name="Dante", text="Hello world!")
await collection.insert(obj)
```

### Find

Finds documents in the collection. There are two variants of the `find` method:

- `find_many` returns a list of documents that match the specified criteria.
- `find_one` returns a single document that matches the specified criteria, or None if no document matches.

Sync:

```python
result = collection.find_one(name="Dante")
```

Async:

```python
result = await collection.find_one(name="Dante")
```

You may specify the limit as the first (positional) argument to `find_many`:

```python
results = collection.find_many(10, name="Dante")
```

Note that Dante currently does not support odering, so limit is of limited use.

Both `find_one` and `find_many` accept keyword arguments for the search criteria. The criteria are matched against the document fields, and the document is returned if all criteria match. If no criteria are specified, all documents are returned.

You can also match against nested fields:

```python
result = collection.find_one(nested__field="value")
```

### Update

Updates matching document(s) in the collection with the specified document.
Note that this will overwrite the existing document(s) with the new data. To
update only specific field(s), use the `set()` method instead.

The function returns the number of documents updated.

Sync with Python dict:

```python
collection.update({"name": "Virgil"}, name="Dante")
```

Sync with Pydantic model:

```python
obj = MyPydanticModel(name="Virgil", text="Hello world!")
collection.update(obj, name="Dante")
```

Async with Python dict:

```python
await collection.update({"name": "Virgil"}, name="Dante")
```

Async with Pydantic model:

```python
obj = MyPydanticModel(name="Virgil", text="Hello world!")
await collection.update(obj, name="Dante")
```

The documents are matches using the same criteria as in `find_one` and `find_many`.
Note that multiple documents may be updated if the criteria match multiple documents.

### Set

Updates fields in matching document(s). This method is useful when you want to update only specific fields. The first argument should be a dictionary with the fields to
update. Note that you can't use Pydantic models with this method, and you can't
delete (remove) fields with this method. For that, use `update()` method instead.

The function returns the number of documents updated.

Sync:

```python
collection.set({"name": "Virgil", "text": "Goodbye!"}, name="Dante")
```

Async:

```python
await collection.set({"name": "Virgil", "text": "Goodbye!"}, name="Dante")
```

The documents are matches using the same criteria as in `find_one` and `find_many`.
Note that multiple documents may be updated if the criteria match multiple documents.

### Delete

Deletes matching document(s) from the collection.

Returns the number of documents deleted.

Sync:

```python
collection.delete(name="Dante")
```

Async:

```python
await collection.delete(name="Dante")
```

The documents are matches using the same criteria as in `find_one` and `find_many`.
Note that multiple documents may be deleted if the criteria match multiple documents.

### Clear

Deletes all documents from the collection.

Returns the number of documents deleted.
