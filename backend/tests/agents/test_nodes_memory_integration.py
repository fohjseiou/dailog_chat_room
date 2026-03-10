"""Test memory integration in response_generator_node"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.agents.nodes import response_generator_node, _enhance_prompt_with_memory
from app.agents.state import AgentState
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.models.user_preference import UserPreference
from datetime import datetime


@pytest.mark.asyncio
async def test_response_generator_with_user_memory(db_session):
    """Test response generator retrieves and uses memory for authenticated user"""
    # Create test user
    user = User(username="memoryuser", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create previous sessions with messages
    session1 = Session(
        id="session1",
        user_id=user.id,
        title="Previous Contract Question",
        message_count=2
    )
    session2 = Session(
        id="session2",
        user_id=user.id,
        title="Employment Law Query",
        message_count=2
    )
    db_session.add_all([session1, session2])
    await db_session.commit()

    # Add messages to sessions
    msg1 = Message(
        session_id=session1.id,
        role="user",
        content="什么是劳动合同？"
    )
    msg2 = Message(
        session_id=session1.id,
        role="assistant",
        content="劳动合同是用人单位与劳动者之间建立劳动关系的协议..."
    )
    msg3 = Message(
        session_id=session2.id,
        role="user",
        content="合同违约怎么办？"
    )
    msg4 = Message(
        session_id=session2.id,
        role="assistant",
        content="合同违约可以要求赔偿损失..."
    )
    db_session.add_all([msg1, msg2, msg3, msg4])
    await db_session.commit()

    # Add user preferences
    pref1 = UserPreference(
        user_id=user.id,
        key="response_style",
        value="detailed"
    )
    pref2 = UserPreference(
        user_id=user.id,
        key="language",
        value="中文"
    )
    db_session.add_all([pref1, pref2])
    await db_session.commit()

    # Mock MemoryService methods
    with patch('app.agents.nodes.MemoryService') as MockMemoryService:
        # Configure mock to return test data
        mock_memory_instance = AsyncMock()
        MockMemoryService.return_value = mock_memory_instance

        mock_memory_instance.get_short_term_context.return_value = [
            {
                "session_id": "session2",
                "title": "Employment Law Query",
                "message_count": 2,
                "messages": [
                    {"role": "user", "content": "合同违约怎么办？"},
                    {"role": "assistant", "content": "合同违约可以要求赔偿损失..."}
                ]
            }
        ]

        mock_memory_instance.get_long_term_memory.return_value = [
            {
                "fact": "用户对劳动法和合同法感兴趣",
                "metadata": {"type": "user_interest"},
                "distance": 0.25
            }
        ]

        mock_memory_instance.get_preferences.return_value = {
            "response_style": "detailed",
            "language": "中文"
        }

        # Create state with user_id
        state = AgentState(
            user_message="劳动合同必须包含哪些条款？",
            conversation_history=[],
            user_intent="legal_consultation",
            retrieved_context=[],
            context_str="劳动合同应当以书面形式订立...",
            sources=[],
            response=None,
            error=None,
            user_id=user.id
        )

        # Execute node
        result = await response_generator_node(state)

        # Verify memory was retrieved
        mock_memory_instance.get_short_term_context.assert_called_once_with(user_id=user.id, limit=3)
        mock_memory_instance.get_long_term_memory.assert_called_once()
        mock_memory_instance.get_preferences.assert_called_once_with(user_id=user.id)

        # Verify response was generated
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
        assert result.get("error") == ""


@pytest.mark.asyncio
async def test_response_generator_without_user(db_session):
    """Test response generator works without user (anonymous user)"""
    # Create state without user_id
    state = AgentState(
        user_message="什么是合同？",
        conversation_history=[],
        user_intent="legal_consultation",
        retrieved_context=[],
        context_str="合同是法律文件...",
        sources=[],
        response=None,
        error=None,
        user_id=None
    )

    # Mock MemoryService to ensure it's not called
    with patch('app.agents.nodes.MemoryService') as MockMemoryService:
        # Execute node
        result = await response_generator_node(state)

        # Verify MemoryService was not instantiated
        MockMemoryService.assert_not_called()

        # Verify response was still generated
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_enhance_prompt_with_memory_full_context(db_session):
    """Test _enhance_prompt_with_memory with all memory types"""
    with patch('app.agents.nodes.MemoryService') as MockMemoryService:
        mock_memory_instance = AsyncMock()
        MockMemoryService.return_value = mock_memory_instance

        # Mock memory retrieval
        mock_memory_instance.get_short_term_context.return_value = [
            {
                "session_id": "prev_session",
                "title": "Previous Discussion",
                "message_count": 2,
                "messages": [
                    {"role": "user", "content": "工伤赔偿标准是什么？"},
                    {"role": "assistant", "content": "工伤赔偿包括医疗费、误工费等..."}
                ]
            }
        ]

        mock_memory_instance.get_long_term_memory.return_value = [
            {
                "fact": "用户关注劳动权益保护问题",
                "metadata": {"type": "user_interest"}
            }
        ]

        mock_memory_instance.get_preferences.return_value = {
            "response_style": "concise",
            "language": "中文"
        }

        base_prompt = "你是一个专业的法律咨询助手。"

        # Call helper function
        enhanced_prompt = await _enhance_prompt_with_memory(
            base_prompt=base_prompt,
            user_id="test_user_id",
            user_message="当前工伤赔偿是多少？",
            db=db_session
        )

        # Verify memory methods were called
        mock_memory_instance.get_short_term_context.assert_called_once()
        mock_memory_instance.get_long_term_memory.assert_called_once()
        mock_memory_instance.get_preferences.assert_called_once()

        # Verify prompt was enhanced
        assert "短期记忆" in enhanced_prompt or "previous" in enhanced_prompt.lower()
        assert isinstance(enhanced_prompt, str)
        assert len(enhanced_prompt) > len(base_prompt)


@pytest.mark.asyncio
async def test_enhance_prompt_with_memory_empty_results(db_session):
    """Test _enhance_prompt_with_memory when memory returns empty results"""
    with patch('app.agents.nodes.MemoryService') as MockMemoryService:
        mock_memory_instance = AsyncMock()
        MockMemoryService.return_value = mock_memory_instance

        # Mock empty memory retrieval
        mock_memory_instance.get_short_term_context.return_value = []
        mock_memory_instance.get_long_term_memory.return_value = []
        mock_memory_instance.get_preferences.return_value = {}

        base_prompt = "你是一个专业的法律咨询助手。"

        # Call helper function
        enhanced_prompt = await _enhance_prompt_with_memory(
            base_prompt=base_prompt,
            user_id="new_user_id",
            user_message="你好",
            db=db_session
        )

        # Verify memory methods were still called
        mock_memory_instance.get_short_term_context.assert_called_once()
        mock_memory_instance.get_long_term_memory.assert_called_once()
        mock_memory_instance.get_preferences.assert_called_once()

        # Verify prompt is still valid (no errors)
        assert isinstance(enhanced_prompt, str)
        assert len(enhanced_prompt) >= len(base_prompt)


@pytest.mark.asyncio
async def test_enhance_prompt_with_memory_service_error(db_session):
    """Test _enhance_prompt_with_memory handles MemoryService errors gracefully"""
    with patch('app.agents.nodes.MemoryService') as MockMemoryService:
        mock_memory_instance = AsyncMock()
        MockMemoryService.return_value = mock_memory_instance

        # Mock service to raise exception
        mock_memory_instance.get_short_term_context.side_effect = Exception("Database error")

        base_prompt = "你是一个专业的法律咨询助手。"

        # Call helper function - should handle error gracefully
        enhanced_prompt = await _enhance_prompt_with_memory(
            base_prompt=base_prompt,
            user_id="error_user_id",
            user_message="测试问题",
            db=db_session
        )

        # Verify base prompt is returned (error handling)
        assert enhanced_prompt == base_prompt


@pytest.mark.asyncio
async def test_response_generator_memory_integration_e2e(db_session):
    """End-to-end test: response generator with real memory integration"""
    # Create user with complete history
    user = User(username="e2e_user", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Create historical session
    session = Session(
        id="e2e_session",
        user_id=user.id,
        title="Legal History",
        message_count=2
    )
    db_session.add(session)
    await db_session.commit()

    msg = Message(
        session_id=session.id,
        role="user",
        content="之前问过关于合同的问题"
    )
    db_session.add(msg)
    await db_session.commit()

    # Create preference
    pref = UserPreference(
        user_id=user.id,
        key="preferred_length",
        value="medium"
    )
    db_session.add(pref)
    await db_session.commit()

    # Mock the database dependency in nodes.py
    with patch('app.agents.nodes.get_db') as mock_get_db:
        mock_get_db.return_value = db_session

        # Mock LLM service
        with patch('app.agents.nodes.get_llm_service') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.llm = AsyncMock()
            mock_llm.llm.ainvoke = AsyncMock(return_value="这是基于您历史记录的回答。")
            mock_get_llm.return_value = mock_llm

            # Create state
            state = AgentState(
                user_message="继续讨论合同问题",
                conversation_history=[],
                user_intent="legal_consultation",
                retrieved_context=[],
                context_str="",
                sources=[],
                response=None,
                error=None,
                user_id=user.id
            )

            # Execute
            result = await response_generator_node(state)

            # Verify response
            assert "response" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0
