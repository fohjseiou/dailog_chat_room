"""Tests for MemoryService"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.memory_service import MemoryService
from app.models.session import Session
from app.models.message import Message
from app.models.user_preference import UserPreference
from datetime import datetime


@pytest.mark.asyncio
async def test_get_short_term_context_with_sessions(db_session: AsyncSession):
    """Test retrieving recent sessions for a user"""
    service = MemoryService(db_session)

    # Create test user
    user_id = str(uuid4())

    # Create multiple sessions for the user
    for i in range(5):
        session = Session(title=f"Session {i}", user_id=user_id)
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Add messages to sessions
        for j in range(2):
            message = Message(
                session_id=session.id,
                role="user",
                content=f"Message {j} in session {i}",
                user_id=user_id
            )
            db_session.add(message)
    await db_session.commit()

    # Get last 3 sessions
    context = await service.get_short_term_context(user_id, limit=3)

    assert len(context) == 3
    assert all("session_id" in c for c in context)
    assert all("title" in c for c in context)
    assert all("messages" in c for c in context)


@pytest.mark.asyncio
async def test_get_short_term_context_no_sessions(db_session: AsyncSession):
    """Test retrieving context for new user with no sessions"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    context = await service.get_short_term_context(user_id)

    assert context == []


@pytest.mark.asyncio
async def test_get_short_term_context_user_isolation(db_session: AsyncSession):
    """Test that users only get their own sessions"""
    service = MemoryService(db_session)

    user1_id = str(uuid4())
    user2_id = str(uuid4())

    # Create session for user1
    session1 = Session(title="User1 Session", user_id=user1_id)
    db_session.add(session1)
    await db_session.commit()

    # Create session for user2
    session2 = Session(title="User2 Session", user_id=user2_id)
    db_session.add(session2)
    await db_session.commit()

    # User1 should only get their own session
    context1 = await service.get_short_term_context(user1_id)
    assert len(context1) == 1
    assert context1[0]["title"] == "User1 Session"

    # User2 should only get their own session
    context2 = await service.get_short_term_context(user2_id)
    assert len(context2) == 1
    assert context2[0]["title"] == "User2 Session"


@pytest.mark.asyncio
async def test_save_user_fact(db_session: AsyncSession):
    """Test saving a user fact to ChromaDB"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    # Mock ChromaService
    with patch.object(service, '_chroma_service') as mock_chroma:
        mock_chroma.add_documents = AsyncMock()

        fact = "User prefers concise answers"
        metadata = {"type": "preference", "confidence": 0.9}

        await service.save_user_fact(user_id, fact, metadata)

        # Verify add_documents was called
        mock_chroma.add_documents.assert_called_once()
        call_args = mock_chroma.add_documents.call_args

        assert call_args[1]["documents"] == [fact]
        assert call_args[1]["metadatas"][0]["user_id"] == user_id
        assert call_args[1]["metadatas"][0]["type"] == "preference"


@pytest.mark.asyncio
async def test_save_conversation_summary(db_session: AsyncSession):
    """Test saving a conversation summary to ChromaDB"""
    service = MemoryService(db_session)
    user_id = str(uuid4())
    session_id = str(uuid4())

    # Mock ChromaService
    with patch.object(service, '_chroma_service') as mock_chroma:
        mock_chroma.add_documents = AsyncMock()

        summary = "Discussion about contract law basics"

        await service.save_conversation_summary(user_id, session_id, summary)

        # Verify add_documents was called
        mock_chroma.add_documents.assert_called_once()
        call_args = mock_chroma.add_documents.call_args

        assert call_args[1]["documents"] == [summary]
        assert call_args[1]["metadatas"][0]["user_id"] == user_id
        assert call_args[1]["metadatas"][0]["session_id"] == session_id
        assert call_args[1]["metadatas"][0]["type"] == "summary"


@pytest.mark.asyncio
async def test_get_long_term_memory_with_embeddings(db_session: AsyncSession):
    """Test retrieving long-term memories using embeddings"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    # Mock ChromaService search
    with patch.object(service, '_chroma_service') as mock_chroma:
        mock_chroma.search = AsyncMock(return_value={
            "documents": ["User is interested in contract law", "User prefers detailed explanations"],
            "metadatas": [
                {"user_id": user_id, "type": "fact", "timestamp": "2024-01-01"},
                {"user_id": user_id, "type": "preference", "timestamp": "2024-01-02"}
            ],
            "distances": [0.1, 0.2]
        })

        # Mock embedding service
        with patch("app.services.memory_service.get_embedding_service") as mock_embedding:
            mock_embedding_instance = AsyncMock()
            mock_embedding_instance.generate_embedding = AsyncMock(return_value=[0.1] * 1024)
            mock_embedding.return_value = mock_embedding_instance

            memories = await service.get_long_term_memory(user_id, "contract law", top_k=5)

            assert len(memories) == 2
            assert "fact" in memories[0]
            assert "metadata" in memories[0]
            assert memories[0]["metadata"]["type"] in ["fact", "preference"]


@pytest.mark.asyncio
async def test_get_long_term_memory_no_embeddings(db_session: AsyncSession):
    """Test retrieving long-term memories when embeddings unavailable"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    # Mock ChromaService to return empty results
    with patch.object(service, '_chroma_service') as mock_chroma:
        mock_chroma.search = AsyncMock(return_value={
            "documents": [],
            "metadatas": [],
            "distances": []
        })

        memories = await service.get_long_term_memory(user_id, "test query")

        assert memories == []


@pytest.mark.asyncio
async def test_get_preferences_no_preferences(db_session: AsyncSession):
    """Test getting preferences for new user"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    preferences = await service.get_preferences(user_id)

    assert preferences == {}


@pytest.mark.asyncio
async def test_set_and_get_preferences(db_session: AsyncSession):
    """Test setting and getting user preferences"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    # Set preferences
    await service.set_preference(user_id, "theme", "dark")
    await service.set_preference(user_id, "language", "en")

    # Get preferences
    preferences = await service.get_preferences(user_id)

    assert preferences["theme"] == "dark"
    assert preferences["language"] == "en"


@pytest.mark.asyncio
async def test_set_preference_updates_existing(db_session: AsyncSession):
    """Test that set_preference updates existing preference"""
    service = MemoryService(db_session)
    user_id = str(uuid4())

    # Set initial preference
    await service.set_preference(user_id, "theme", "dark")

    # Update preference
    await service.set_preference(user_id, "theme", "light")

    # Get preferences
    preferences = await service.get_preferences(user_id)

    assert preferences["theme"] == "light"


@pytest.mark.asyncio
async def test_get_long_term_memory_user_isolation(db_session: AsyncSession):
    """Test that users only get their own long-term memories"""
    service = MemoryService(db_session)

    user1_id = str(uuid4())
    user2_id = str(uuid4())

    # Mock ChromaService to return user1's memories
    with patch.object(service, '_chroma_service') as mock_chroma:
        mock_chroma.search = AsyncMock(return_value={
            "documents": ["User1 fact"],
            "metadatas": [{"user_id": user1_id, "type": "fact"}],
            "distances": [0.1]
        })

        memories = await service.get_long_term_memory(user2_id, "test")

        # Should be empty since Chroma returns user1's data but service filters by user_id
        assert memories == []
