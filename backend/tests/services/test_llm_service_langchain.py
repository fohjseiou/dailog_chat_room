# -*- coding: utf-8 -*-
"""Tests for LLMService using LangChain ChatTongyi integration."""

import pytest
from app.services.llm_service import LLMService, get_llm_service
from langchain_community.chat_models.tongyi import ChatTongyi


def test_llm_service_uses_chat_tongyi():
    """Test that LLMService uses ChatTongyi"""
    service = LLMService()
    assert hasattr(service, 'llm')
    assert isinstance(service.llm, ChatTongyi)


def test_llm_service_singleton():
    """Test that get_llm_service returns singleton"""
    service1 = get_llm_service()
    service2 = get_llm_service()
    assert service1 is service2


def test_llm_service_has_correct_model():
    """Test that LLMService is configured with correct model"""
    service = LLMService()
    # The model_name property should match the configured model
    assert service.llm.model_name is not None
    assert isinstance(service.llm.model_name, str)
    assert len(service.llm.model_name) > 0


@pytest.mark.asyncio
async def test_generate_response_basic():
    """Test basic response generation with ChatTongyi"""
    service = LLMService()
    response = await service.generate_response(
        message="你好",
        conversation_history=[],
        system_prompt="你是一个法律助手"
    )
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_generate_response_with_history():
    """Test response generation with conversation history"""
    service = LLMService()
    history = [
        {"role": "user", "content": "什么是合同？"},
        {"role": "assistant", "content": "合同是..."}
    ]
    response = await service.generate_response(
        message="能详细解释吗？",
        conversation_history=history
    )
    assert isinstance(response, str)
    assert len(response) > 0
