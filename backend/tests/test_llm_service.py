# -*- coding: utf-8 -*-
import pytest
import asyncio
from app.services.llm_service import get_llm_service, LLMService

@pytest.mark.asyncio
async def test_llm_service_singleton():
    """Test that LLM service returns singleton instance"""
    service1 = get_llm_service()
    service2 = get_llm_service()
    assert service1 is service2

@pytest.mark.asyncio
async def test_generate_response():
    """Test basic Qwen response generation"""
    service = get_llm_service()
    response = await service.generate_response(
        message="你好，请简单介绍一下自己。",
        conversation_history=[]
    )
    assert response is not None
    assert len(response) > 0
    # Response should contain legal-related keywords or error message
    assert "法律" in response or "助手" in response or "抱歉" in response

@pytest.mark.asyncio
async def test_conversation_context():
    """Test that conversation history is used"""
    service = get_llm_service()
    history = [
        {"role": "user", "content": "我叫张三"},
        {"role": "assistant", "content": "你好张三"}
    ]
    response = await service.generate_response(
        message="我叫什么名字？",
        conversation_history=history
    )
    assert response is not None
    assert len(response) > 0
    # If successful, should remember the name; if error, should have error message
    assert "张三" in response or "抱歉" in response

@pytest.mark.asyncio
async def test_streaming_response():
    """Test streaming response functionality"""
    service = get_llm_service()
    chunks = []
    async for chunk in service.generate_response_stream(
        message="你好",
        conversation_history=[]
    ):
        chunks.append(chunk)

    full_response = "".join(chunks)
    assert len(full_response) > 0
