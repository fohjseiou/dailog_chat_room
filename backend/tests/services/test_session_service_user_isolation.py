import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate
from app.models.user import User
from passlib.context import CryptContext


@pytest.mark.asyncio
async def test_create_session_with_user(db_session: AsyncSession):
    """Test creating a session with a user_id"""
    service = SessionService(db_session)

    # Create a test user
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("testpassword")
    user = User(username="testuser", password_hash=hashed)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create session with user_id
    data = SessionCreate(title="Test Session")
    session = await service.create_session(data, user_id=str(user.id))

    assert session.id is not None
    assert session.title == "Test Session"
    assert session.user_id == str(user.id)
    assert session.message_count == 0


@pytest.mark.asyncio
async def test_create_session_without_user_anonymous(db_session: AsyncSession):
    """Test creating a session without a user_id (anonymous)"""
    service = SessionService(db_session)

    # Create session without user_id
    data = SessionCreate(title="Anonymous Session")
    session = await service.create_session(data, user_id=None)

    assert session.id is not None
    assert session.title == "Anonymous Session"
    assert session.user_id is None
    assert session.message_count == 0


@pytest.mark.asyncio
async def test_create_session_default_no_user(db_session: AsyncSession):
    """Test creating a session defaults to no user_id when not provided"""
    service = SessionService(db_session)

    # Create session without providing user_id parameter
    data = SessionCreate(title="Default Session")
    session = await service.create_session(data)

    assert session.id is not None
    assert session.title == "Default Session"
    assert session.user_id is None
    assert session.message_count == 0


@pytest.mark.asyncio
async def test_list_sessions_filters_by_user_id(db_session: AsyncSession):
    """Test that list_sessions filters by user_id when provided"""
    service = SessionService(db_session)

    # Create two users
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user1 = User(username="user1", password_hash=pwd_context.hash("password1"))
    user2 = User(username="user2", password_hash=pwd_context.hash("password2"))
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Create sessions for user1
    await service.create_session(SessionCreate(title="User1 Session 1"), user_id=str(user1.id))
    await service.create_session(SessionCreate(title="User1 Session 2"), user_id=str(user1.id))

    # Create sessions for user2
    await service.create_session(SessionCreate(title="User2 Session 1"), user_id=str(user2.id))

    # Create anonymous session
    await service.create_session(SessionCreate(title="Anonymous Session"), user_id=None)

    # List only user1's sessions
    user1_sessions = await service.list_sessions(user_id=str(user1.id))

    assert len(user1_sessions) == 2
    assert all(s.user_id == str(user1.id) for s in user1_sessions)
    assert any(s.title == "User1 Session 1" for s in user1_sessions)
    assert any(s.title == "User1 Session 2" for s in user1_sessions)

    # List only user2's sessions
    user2_sessions = await service.list_sessions(user_id=str(user2.id))

    assert len(user2_sessions) == 1
    assert user2_sessions[0].user_id == str(user2.id)
    assert user2_sessions[0].title == "User2 Session 1"


@pytest.mark.asyncio
async def test_list_sessions_all_when_user_id_none(db_session: AsyncSession):
    """Test that list_sessions returns all sessions when user_id is None"""
    service = SessionService(db_session)

    # Create two users
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user1 = User(username="user1", password_hash=pwd_context.hash("password1"))
    user2 = User(username="user2", password_hash=pwd_context.hash("password2"))
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Create sessions for user1
    await service.create_session(SessionCreate(title="User1 Session 1"), user_id=str(user1.id))

    # Create sessions for user2
    await service.create_session(SessionCreate(title="User2 Session 1"), user_id=str(user2.id))

    # Create anonymous session
    await service.create_session(SessionCreate(title="Anonymous Session"), user_id=None)

    # List all sessions (user_id=None)
    all_sessions = await service.list_sessions(user_id=None)

    assert len(all_sessions) == 3
    assert any(s.user_id == str(user1.id) for s in all_sessions)
    assert any(s.user_id == str(user2.id) for s in all_sessions)
    assert any(s.user_id is None for s in all_sessions)


@pytest.mark.asyncio
async def test_list_sessions_default_all(db_session: AsyncSession):
    """Test that list_sessions returns all sessions when user_id parameter is not provided"""
    service = SessionService(db_session)

    # Create two users
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user1 = User(username="user1", password_hash=pwd_context.hash("password1"))
    user2 = User(username="user2", password_hash=pwd_context.hash("password2"))
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Create sessions for user1
    await service.create_session(SessionCreate(title="User1 Session 1"), user_id=str(user1.id))

    # Create sessions for user2
    await service.create_session(SessionCreate(title="User2 Session 1"), user_id=str(user2.id))

    # Create anonymous session
    await service.create_session(SessionCreate(title="Anonymous Session"), user_id=None)

    # List all sessions (no user_id parameter)
    all_sessions = await service.list_sessions()

    assert len(all_sessions) == 3
    assert any(s.user_id == str(user1.id) for s in all_sessions)
    assert any(s.user_id == str(user2.id) for s in all_sessions)
    assert any(s.user_id is None for s in all_sessions)
