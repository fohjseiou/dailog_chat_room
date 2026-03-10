import pytest
from app.models.session import Session
from app.models.user import User

@pytest.mark.asyncio
async def test_session_with_user(db_session):
    user = User(username="testuser", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    session = Session(title="Test Session", user_id=user.id)
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.user_id == user.id
    assert session.user is not None
    assert session.user.username == "testuser"

@pytest.mark.asyncio
async def test_session_without_user(db_session):
    session = Session(title="Anonymous Session")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.user_id is None
    assert session.user is None
