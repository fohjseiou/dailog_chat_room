import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionUpdate


@pytest.mark.asyncio
async def test_create_session(db_session: AsyncSession):
    service = SessionService(db_session)
    data = SessionCreate(title="Test Session")

    session = await service.create_session(data)

    assert session.id is not None
    assert session.title == "Test Session"
    assert session.message_count == 0


@pytest.mark.asyncio
async def test_list_sessions(db_session: AsyncSession):
    service = SessionService(db_session)

    for i in range(3):
        await service.create_session(SessionCreate(title=f"Session {i}"))

    sessions = await service.list_sessions()

    assert len(sessions) == 3
    assert all(s.id is not None for s in sessions)


@pytest.mark.asyncio
async def test_get_session(db_session: AsyncSession):
    service = SessionService(db_session)
    created = await service.create_session(SessionCreate(title="Test"))

    session = await service.get_session(created.id)

    assert session is not None
    assert session.id == created.id
    assert session.title == "Test"


@pytest.mark.asyncio
async def test_update_session(db_session: AsyncSession):
    service = SessionService(db_session)
    created = await service.create_session(SessionCreate(title="Old Title"))

    updated = await service.update_session(created.id, SessionUpdate(title="New Title"))

    assert updated.title == "New Title"


@pytest.mark.asyncio
async def test_delete_session(db_session: AsyncSession):
    service = SessionService(db_session)
    created = await service.create_session(SessionCreate(title="ToDelete"))

    await service.delete_session(created.id)

    session = await service.get_session(created.id)
    assert session is None
