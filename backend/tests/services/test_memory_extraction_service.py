"""Tests for MemoryExtractionService"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.memory_extraction_service import MemoryExtractionService
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.models.user import User


@pytest.mark.asyncio
async def test_should_extract_facts_with_keywords(db_session: AsyncSession):
    """Test fact extraction trigger with keywords"""
    service = MemoryExtractionService(db_session)

    # Should return True for messages with keywords
    assert service.should_extract_facts("我是律师") is True
    assert service.should_extract_facts("我叫张三") is True
    assert service.should_extract_facts("我的工作是工程师") is True
    assert service.should_extract_facts("我喜欢简洁的回答") is True

    # Should return False for messages without keywords
    assert service.should_extract_facts("请问合同法怎么规定") is False
    assert service.should_extract_facts("谢谢你的回答") is False


@pytest.mark.asyncio
async def test_should_extract_facts_without_keywords(db_session: AsyncSession):
    """Test fact extraction trigger without keywords"""
    service = MemoryExtractionService(db_session)

    # Generic legal questions should not trigger extraction
    assert service.should_extract_facts("劳动合同法有规定吗") is False
    assert service.should_extract_facts("如何申请仲裁") is False


@pytest.mark.asyncio
async def test_extract_and_store_facts(db_session: AsyncSession):
    """Test fact extraction and storage"""
    # Create a test user
    user = User(username="testuser_facts", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Create a session
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"}, user_id=user.id)

    service = MemoryExtractionService(db_session)

    conversation_text = """
    用户：我是执业律师，专精合同法
    助手：您好，很高兴为您服务
    用户：我偏好简洁专业的回答
    助手：明白了，我会注意
    """

    facts = await service.extract_and_store_facts(user.id, session.id, conversation_text)

    # Should extract some facts (LLM-dependent, so we just check it runs)
    assert isinstance(facts, list)


@pytest.mark.asyncio
async def test_generate_and_store_summary(db_session: AsyncSession):
    """Test conversation summary generation and storage"""
    # Create a test user
    user = User(username="testuser_summary", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Create a session with messages
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"}, user_id=user.id)

    message_service = MessageService(db_session)
    await message_service.save_exchange(
        session.id,
        "劳动合同纠纷怎么办",
        "根据劳动合同法，您可以申请仲裁...",
        {}
    )
    await message_service.save_exchange(
        session.id,
        "需要什么证据",
        "您需要准备劳动合同、工资条等证据...",
        {}
    )

    service = MemoryExtractionService(db_session)
    summary = await service.generate_and_store_summary(user.id, session.id)

    # Summary should be generated
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0


@pytest.mark.asyncio
async def test_process_conversation_memory_at_10_rounds(db_session: AsyncSession):
    """Test memory processing every 10 rounds"""
    # Create a test user
    user = User(username="testuser_10rounds", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Create a session
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"}, user_id=user.id)

    # Add 10 messages
    message_service = MessageService(db_session)
    for i in range(10):
        await message_service.save_exchange(
            session.id,
            f"问题 {i+1}",
            f"回答 {i+1}",
            {}
        )

    service = MemoryExtractionService(db_session)
    results = await service.process_conversation_memory(
        user_id=user.id,
        session_id=session.id,
        message_count=10,
        last_user_message="问题 10",
        last_n_messages=[{"role": "user", "content": "问题 10"}]
    )

    # At 10 rounds, summary should be generated
    assert "summary_generated" in results
    assert "facts_extracted" in results


@pytest.mark.asyncio
async def test_process_conversation_memory_with_keywords(db_session: AsyncSession):
    """Test memory processing triggered by keywords"""
    # Create a test user
    user = User(username="testuser_keywords", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Create a session
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"}, user_id=user.id)

    service = MemoryExtractionService(db_session)

    # Message with "我是" keyword
    results = await service.process_conversation_memory(
        user_id=user.id,
        session_id=session.id,
        message_count=1,
        last_user_message="我是律师，请问合同法...",
        last_n_messages=[{"role": "user", "content": "我是律师，请问合同法..."}]
    )

    # Facts should be extracted due to keyword
    assert "facts_extracted" in results
    assert isinstance(results["facts_extracted"], list)


@pytest.mark.asyncio
async def test_process_conversation_memory_without_user(db_session: AsyncSession):
    """Test that memory processing is skipped for anonymous users"""
    # Create a session without user
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"}, user_id=None)

    service = MemoryExtractionService(db_session)
    results = await service.process_conversation_memory(
        user_id=None,  # Anonymous user
        session_id=session.id,
        message_count=10,
        last_user_message="我是律师",
        last_n_messages=[{"role": "user", "content": "我是律师"}]
    )

    # Should return empty results for anonymous users
    assert results["facts_extracted"] == []
    assert results["summary_generated"] is None
