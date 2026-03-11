"""Tests for memory_extraction_node"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from app.agents.nodes import memory_extraction_node
from app.agents.state import create_initial_state


@pytest.mark.asyncio
async def test_memory_extraction_skipped_for_anonymous_user(db_session):
    """Test that memory extraction is skipped for anonymous users"""
    state = create_initial_state(
        user_message="Test message",
        conversation_history=[],
        user_id=None,  # Anonymous
        session_id="test-session"
    )

    result = await memory_extraction_node(state)

    assert result["memory_extracted"] is False
    assert result["facts_extracted"] == []


@pytest.mark.asyncio
async def test_memory_extraction_executes_for_authenticated_user(db_session):
    """Test that memory extraction executes for authenticated users"""
    user_id = "test-user-123"
    session_id = "test-session-456"

    state = create_initial_state(
        user_message="我是律师，专精合同法",
        conversation_history=[
            {"role": "assistant", "content": "您好，有什么可以帮助您的？"}
        ],
        user_id=user_id,
        session_id=session_id
    )

    # Mock the services
    with patch('app.agents.nodes.MemoryExtractionService') as MockMemoryExtraction:
        mock_service = AsyncMock()
        mock_service.process_conversation_memory = AsyncMock(return_value={
            "facts_extracted": ["用户是执业律师"],
            "summary_generated": "讨论合同法相关问题"
        })
        MockMemoryExtraction.return_value = mock_service

        with patch('app.agents.nodes.SessionService') as MockSessionService:
            mock_session_service = AsyncMock()
            mock_session = Mock()
            mock_session.message_count = 5
            mock_session_service.get_session = AsyncMock(return_value=mock_session)
            MockSessionService.return_value = mock_session_service

            result = await memory_extraction_node(state)

    assert result["memory_extracted"] is True
    assert len(result["facts_extracted"]) > 0
    assert result["summary_generated"] is not None


@pytest.mark.asyncio
async def test_memory_extraction_handles_session_not_found(db_session):
    """Test that memory extraction handles session not found gracefully"""
    state = create_initial_state(
        user_message="Test",
        conversation_history=[],
        user_id="test-user",
        session_id="non-existent-session"
    )

    result = await memory_extraction_node(state)

    # Should handle missing session gracefully
    # The node should not crash even if session is not found
    assert "memory_extracted" in result
    assert "facts_extracted" in result
    assert "summary_generated" in result
