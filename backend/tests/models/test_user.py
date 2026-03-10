import pytest
from app.models.user import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_user_model_creation(db_session):
    user = User(username="testuser", password_hash="hashed_password_here")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.password_hash == "hashed_password_here"
    assert user.created_at is not None
    assert user.last_login is None

@pytest.mark.asyncio
async def test_user_username_unique(db_session):
    user1 = User(username="duplicate", password_hash="hash1")
    db_session.add(user1)
    await db_session.commit()

    user2 = User(username="duplicate", password_hash="hash2")
    db_session.add(user2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()
