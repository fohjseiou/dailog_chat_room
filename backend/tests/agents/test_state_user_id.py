"""Tests for AgentState user_id field."""

import pytest
from app.agents.state import AgentState, create_initial_state


def test_agent_state_with_user_id():
    """Test AgentState can be created with user_id field."""
    state = AgentState(
        user_message="Test message",
        conversation_history=[],
        user_intent="general_chat",
        user_id="user123"
    )
    assert state["user_message"] == "Test message"
    assert state["conversation_history"] == []
    assert state["user_intent"] == "general_chat"
    assert state["user_id"] == "user123"


def test_agent_state_without_user_id():
    """Test AgentState can be created without user_id field (backward compatibility)."""
    state = AgentState(
        user_message="Test message",
        conversation_history=[],
        user_intent="general_chat"
    )
    assert state["user_message"] == "Test message"
    assert state["conversation_history"] == []
    assert state["user_intent"] == "general_chat"
    assert state.get("user_id") is None


def test_agent_state_with_none_user_id():
    """Test AgentState can explicitly set user_id to None."""
    state = AgentState(
        user_message="Test message",
        conversation_history=[],
        user_intent="general_chat",
        user_id=None
    )
    assert state["user_message"] == "Test message"
    assert state["user_id"] is None


def test_create_initial_state_with_user_id():
    """Test create_initial_state includes user_id when provided."""
    state = create_initial_state(
        user_message="Hello",
        conversation_history=[{"role": "user", "content": "Hi"}],
        user_id="user456"
    )
    assert state["user_message"] == "Hello"
    assert state["user_id"] == "user456"


def test_create_initial_state_without_user_id():
    """Test create_initial_state works without user_id (backward compatibility)."""
    state = create_initial_state(
        user_message="Hello",
        conversation_history=[]
    )
    assert state["user_message"] == "Hello"
    assert state.get("user_id") is None


def test_agent_state_user_id_type():
    """Test that user_id accepts string values."""
    state = AgentState(
        user_message="Test",
        conversation_history=[],
        user_intent="general_chat",
        user_id="test-user-id"
    )
    assert isinstance(state["user_id"], str)
    assert state["user_id"] == "test-user-id"
