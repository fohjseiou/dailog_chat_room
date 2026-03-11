"""Test Chat API passes user_id to agent state.

Tests for Task 15: Update Chat API to Pass user_id from auth to chat agent.
Tests for Task 4: Simplify non-streaming chat endpoint to use graph.ainvoke()
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.database import get_db
from app.services.token_service import TokenService
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from passlib.context import CryptContext

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def chat_test_db():
    """Create a test database for chat API tests"""
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
def chat_test_client(chat_test_db):
    """Create a test client with test database"""
    async def override_get_db():
        yield chat_test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def chat_test_user(chat_test_db):
    """Create a test user in the same database used by the test client"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("testpassword")
    user = User(username="chattestuser", password_hash=hashed)
    chat_test_db.add(user)
    await chat_test_db.commit()
    await chat_test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_stream_chat_passes_user_id_authenticated(chat_test_client, chat_test_user):
    """Test stream_chat endpoint passes user_id to AgentState when user is authenticated."""

    token_service = TokenService()
    token = token_service.create_access_token(chat_test_user.id)

    call_captures = []

    def spy_create_initial_state(user_message, conversation_history, user_id=None):
        call_captures.append({
            'user_message': user_message,
            'conversation_history': conversation_history,
            'user_id': user_id
        })
        from app.agents.state import create_initial_state as orig
        return orig(user_message, conversation_history, user_id)

    with patch('app.api.v1.chat.create_initial_state', side_effect=spy_create_initial_state):
        with patch('app.agents.nodes.intent_router_node', new_callable=AsyncMock) as mock_intent:
            mock_intent.return_value = {"user_intent": "general"}

            with patch('app.agents.nodes.response_generator_node_stream') as mock_stream:
                async def mock_stream_gen(state):
                    yield {"event": "token", "data": {"content": "test"}}
                    yield {"event": "end", "data": {"response": "test response"}}
                mock_stream.side_effect = mock_stream_gen

                response = chat_test_client.post(
                    "/api/v1/chat/stream",
                    json={"message": "test message"},
                    headers={"Authorization": f"Bearer {token}"}
                )

                assert len(call_captures) > 0, "create_initial_state was not called"
                call_args = call_captures[0]

                assert 'user_id' in call_args
                assert call_args['user_id'] == str(chat_test_user.id), \
                    f"Expected user_id={chat_test_user.id}, got {call_args['user_id']}"


@pytest.mark.asyncio
async def test_stream_chat_passes_none_user_id_anonymous(chat_test_client):
    """Test stream_chat endpoint passes None for user_id when user is anonymous."""

    call_captures = []

    def spy_create_initial_state(user_message, conversation_history, user_id=None):
        call_captures.append({
            'user_message': user_message,
            'conversation_history': conversation_history,
            'user_id': user_id
        })
        from app.agents.state import create_initial_state as orig
        return orig(user_message, conversation_history, user_id)

    with patch('app.api.v1.chat.create_initial_state', side_effect=spy_create_initial_state):
        with patch('app.agents.nodes.intent_router_node', new_callable=AsyncMock) as mock_intent:
            mock_intent.return_value = {"user_intent": "general"}

            with patch('app.agents.nodes.response_generator_node_stream') as mock_stream:
                async def mock_stream_gen(state):
                    yield {"event": "token", "data": {"content": "test"}}
                    yield {"event": "end", "data": {"response": "test response"}}
                mock_stream.side_effect = mock_stream_gen

                response = chat_test_client.post(
                    "/api/v1/chat/stream",
                    json={"message": "test message"}
                )

                assert len(call_captures) > 0, "create_initial_state was not called"
                call_args = call_captures[0]

                assert 'user_id' in call_args
                assert call_args['user_id'] is None, \
                    f"Expected user_id=None, got {call_args['user_id']}"


@pytest.mark.asyncio
async def test_chat_passes_user_id_authenticated(chat_test_client, chat_test_user):
    """Test regular chat endpoint passes user_id to AgentState when user is authenticated."""

    token_service = TokenService()
    token = token_service.create_access_token(chat_test_user.id)

    call_captures = []

    def spy_create_initial_state(user_message, conversation_history, user_id=None, session_id=None, streaming=False):
        call_captures.append({
            'user_message': user_message,
            'conversation_history': conversation_history,
            'user_id': user_id,
            'session_id': session_id,
            'streaming': streaming
        })
        from app.agents.state import create_initial_state as orig
        return orig(user_message, conversation_history, user_id, session_id, streaming)

    with patch('app.api.v1.chat.create_initial_state', side_effect=spy_create_initial_state):
        with patch('app.api.v1.chat.get_unified_agent_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(return_value={
                "response": "test response",
                "sources": [],
                "user_intent": "general",
                "error": None
            })
            mock_get_graph.return_value = mock_graph

            response = chat_test_client.post(
                "/api/v1/chat",
                json={"message": "test message"},
                headers={"Authorization": f"Bearer {token}"}
            )

            assert len(call_captures) > 0, "create_initial_state was not called"
            call_args = call_captures[0]

            assert 'user_id' in call_args
            assert call_args['user_id'] == str(chat_test_user.id), \
                f"Expected user_id={chat_test_user.id}, got {call_args['user_id']}"
            assert call_args['streaming'] is False, "Expected streaming=False for non-streaming endpoint"


@pytest.mark.asyncio
async def test_chat_passes_none_user_id_anonymous(chat_test_client):
    """Test regular chat endpoint passes None for user_id when user is anonymous."""

    call_captures = []

    def spy_create_initial_state(user_message, conversation_history, user_id=None, session_id=None, streaming=False):
        call_captures.append({
            'user_message': user_message,
            'conversation_history': conversation_history,
            'user_id': user_id,
            'session_id': session_id,
            'streaming': streaming
        })
        from app.agents.state import create_initial_state as orig
        return orig(user_message, conversation_history, user_id, session_id, streaming)

    with patch('app.api.v1.chat.create_initial_state', side_effect=spy_create_initial_state):
        with patch('app.api.v1.chat.get_unified_agent_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(return_value={
                "response": "test response",
                "sources": [],
                "user_intent": "general",
                "error": None
            })
            mock_get_graph.return_value = mock_graph

            response = chat_test_client.post(
                "/api/v1/chat",
                json={"message": "test message"}
            )

            assert len(call_captures) > 0, "create_initial_state was not called"
            call_args = call_captures[0]

            assert 'user_id' in call_args
            assert call_args['user_id'] is None, \
                f"Expected user_id=None, got {call_args['user_id']}"
            assert call_args['streaming'] is False, "Expected streaming=False for non-streaming endpoint"


@pytest.mark.asyncio
async def test_chat_with_authenticated_user_uses_graph(chat_test_client, chat_test_user):
    """Test that chat endpoint uses LangGraph for authenticated users"""
    token_service = TokenService()
    token = token_service.create_access_token(chat_test_user.id)

    # Mock the graph's ainvoke method
    with patch('app.api.v1.chat.get_unified_agent_graph') as mock_get_graph:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "这是关于合同违约的法律建议",
            "sources": [{"doc": "合同法相关条款"}],
            "user_intent": "legal_consultation",
            "error": None
        })
        mock_get_graph.return_value = mock_graph

        response = chat_test_client.post(
            "/api/v1/chat",
            json={"message": "合同违约怎么办？"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] is not None
        assert data["response"] == "这是关于合同违约的法律建议"
        assert "sources" in data

        # Verify that ainvoke was called
        mock_graph.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_chat_with_anonymous_user_uses_graph(chat_test_client):
    """Test that chat endpoint uses LangGraph for anonymous users"""
    # Mock the graph's ainvoke method
    with patch('app.api.v1.chat.get_unified_agent_graph') as mock_get_graph:
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "你好！有什么我可以帮助你的吗？",
            "sources": [],
            "user_intent": "greeting",
            "error": None
        })
        mock_get_graph.return_value = mock_graph

        response = chat_test_client.post(
            "/api/v1/chat",
            json={"message": "你好"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] is not None
        assert data["response"] == "你好！有什么我可以帮助你的吗？"

        # Verify that ainvoke was called
        mock_graph.ainvoke.assert_called_once()


