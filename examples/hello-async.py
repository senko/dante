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
