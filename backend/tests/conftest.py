import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def test_db():
    """Create a test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    testing_session_local = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with testing_session_local() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client with test database"""
    from fastapi.testclient import TestClient
    from app.main import app

    async def override_get_db():
        yield test_db

    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    import asyncio

    def sync_wrapper():
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.sleep(0))

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
