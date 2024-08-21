# Dante, a simple database for Python

Dante is a simple, easy to use NoSQL database for Python, ideal for
exploratory programming, prototyping, and small, simple projects.

Dante can store Python dictionaries or Pydantic models, supports both
sync and async mode, and is based on SQLite.

Dante *does not* support SQL, relations, ACID, aggregation, replication and is
emphatically not web-scale. If you need those features, you should choose
another database or ORM engine.

## Quickstart

1. Install via PyPI:

    ```shell
    pip install dante-db
    ```

2. Use it with Python dictionaries:

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
    collection.update_one(new_data, name="Dante")
    ```

Under the hood, Dante stores each dictionary in a JSON-encoded TEXT column
in a table (one per collection) in the SQLite database.

## Use with Pydantic

Dante also works well with Pydantic.

Using the same API as with the plain Python objects, you can insert,
query and delete Pydantic models:

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
collection.update_one(result, name="Dante")
```

There's also a `DanteMixin` model mixin you can apply to your
Pydantic models to enable ORM-like syntax on them:

```python
from dante import Dante, DanteMixin
from pydantic import BaseModel

class Message(DanteMixin, BaseModel):
    name: str
    text: str

# Open the database
DanteMixin.use_db("mydatabase.db")

# Create a new Message model to the database
obj = Message(name="Dante", text="Hello world!")
obj.save()

# Find a model with the specieied attribute(s)
result = Message.find_one(name="Dante")
print(result.text)

# Find a model in the collection with the attribute name=Dante
# and update(overwrite) it with the latest model data
obj.name = "Virgil"
obj.save(name="Dante")

for message in Message.find_many():
    print(message.name, message.text)
```

Note that even with ORM-like syntax, Dante has no concept of
IDs or keys. In the example above, we have to update the existing
object in the database by telling Dante how to find the old object with
`obj.save(namme="Dante")`. Without it, Dante would create a new copy
of the object.

## Aync Dante

Dante can also be used asynchronously with the identical API, both
for plain Python objects and Pydantic models:

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
    await collection.update_one(new_data, name="Dante")

    await db.close()

run(main())
```

It also works in ORM-like mode:

```python
from asyncio import run
from dante import AsyncDanteMixin
from pydantic import BaseModel

class Message(AsyncDanteMixin, BaseModel):
    name: str
    text: str

AsyncDanteMixin.use_db("mydatabase.db")

async def main():
    obj = Message(name="Dante", text="Hello world!")
    await obj.save()

    result = await Message.find_one(name="Dante")
    print(result.text)

    # Find a model in the collection with the attribute name=Dante
    # and update(overwrite) it with the latest model data
    obj.name = "Virgil"
    await obj.save(name="Dante")

    for message in await Message.find_many():
        print(message.name, message.text)

    # Contrary to sync mode, not closing the db explicitly would hang
    # the process at exit.
    await AsyncDanteMixin.close_db()

run(main())
```


## Tests

Run the tests with pytest:

```
pytest --cov=dante
```

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
