import pytest_asyncio

from dante import AsyncDante


@pytest_asyncio.fixture
async def db():
    db = AsyncDante()
    yield db
    await db.close()
