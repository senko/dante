# Dante, a document store for Python backed by SQLite

[![Build](https://github.com/senko/dante/actions/workflows/ci.yml/badge.svg)](https://github.com/senko/dante/actions/workflows/ci.yml)
[![Coverage](https://coveralls.io/repos/github/senko/dante/badge.svg?branch=main)](https://coveralls.io/github/senko/dante?branch=main)
[![PyPI](https://img.shields.io/pypi/v/dante-db)](https://pypi.org/project/dante-db/)

Dante is zero-setup, easy to use document store (NoSQL database) for Python.
It's ideal for exploratory programming, prototyping, internal tools and
small, simple projects.

Dante can store Python dictionaries or Pydantic models, supports both
sync and async mode, and is based on SQLite.

Dante *does not* support SQL, relations, ACID, aggregation, replication and is
emphatically not web-scale. If you need those features, you should choose
another database or ORM engine.

* [Quickstart](#quickstart)
* [API Reference](docs/api.md)
* [Examples](#examples)

## Quickstart

1. Install via PyPI:

    ```shell
    pip install dante-db
    ```

2. Use it with Python dictionaries ([example](examples/hello.py)):

    ```python
    from dante import Dante

    # Create 'mydatabase.db' in current directory and open it
    # (you can omit the database name to create a temporary in-memory database.)
    db = Dante("mydatabase.db")

    # Use 'mycollection' collection (also known as a "table")
    collection = db["mycollection"]

    # Insert a dictionary to the database
    data = {"name": "Dante", "text": "Hello World!"}
    collection.insert(data)

    # Find a dictionary with the specified attribute(s)
    result = collection.find_one(name="Dante")
    print(result["text"])

    new_data = {"name": "Virgil", "text": "Hello World!"}
    collection.update(new_data, name="Dante")
    ```

Under the hood, Dante stores each dictionary in a JSON-encoded TEXT column
in a table (one per collection) in the SQLite database.

## Use with Pydantic

Dante works great with Pydantic.

Using the same API as with the plain Python objects, you can insert,
query and delete Pydantic models ([example](examples/hello-pydantic.py)):

```python
from dante import Dante
from pydantic import BaseModel

class Message(BaseModel):
    name: str
    text: str

# Open the database and get the collection for messages
db = Dante("mydatabase.db")
collection = db[Message]

# Insert a model to the database
obj = Message(name="Dante", text="Hello world!")
collection.insert(obj)

# Find a model with the specified attribute(s)
result = collection.find_one(name="Dante")
print(result.text)

# Find a model in the collection with the attribute name=Dante
# and update (overwrite) it with the new model data
result.name = "Virgil"
collection.update(result, name="Dante")
```

## Async Dante

Dante supports async usage with the identical API, both for plain Python
objects and Pydantic models ([example](examples/hello-async.py)):

```python
from asyncio import run
from dante import AsyncDante

async def main():
    db = AsyncDante("mydatabase.db")
    collection = await db["mycollection"]

    data = {"name": "Dante", "text": "Hello World!"}
    await collection.insert(data)

    result = await collection.find_one(name="Dante")
    print(result["text"])

    new_data = {"name": "Virgil", "text": "Hello World!"}
    await collection.update(new_data, name="Dante")

    await db.close()

run(main())
```

## Examples

Check out the command-line [ToDo app](examples/todo.py),
a simple [FastAPI CRUD app](examples/fastapi-example.py),
and the other examples in the [examples](examples/) directory.

## Development

Detailed guide on how to develop, test and publish Dante is available in the
[Developer documentation](docs/development.md).


## License (MIT)

Copyright (c) 2024. Senko Rasic

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
