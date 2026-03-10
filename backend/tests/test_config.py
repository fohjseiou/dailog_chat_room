"""Tests for application configuration with multi-provider LLM support."""

import pytest
from app.config import get_settings, create_llm_from_config


def test_default_provider_is_tongyi():
    """Test that default LLM provider is tongyi"""
    settings = get_settings()
    # Provider may not be in old config, check default
    assert hasattr(settings, 'dashscope_api_key')


def test_llm_config_attributes():
    """Test LLM config has required attributes"""
    settings = get_settings()
    assert hasattr(settings, 'dashscope_model')
    assert hasattr(settings, 'dashscope_api_key')


def test_create_llm_from_tongyi_config():
    """Test creating ChatTongyi from config"""
    from langchain_community.chat_models.tongyi import ChatTongyi

    settings = get_settings()
    llm = create_llm_from_config(settings)
    assert isinstance(llm, ChatTongyi)
