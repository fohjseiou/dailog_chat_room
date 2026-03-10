import pytest
from app.agents.state import AgentState

def test_agent_state_creation():
    """Test AgentState can be created with all required fields"""
    state = AgentState(
        user_message="Test message",
        conversation_history=[],
        user_intent="general_chat"
    )
    assert state["user_message"] == "Test message"
    assert state["conversation_history"] == []
    assert state["user_intent"] == "general_chat"

def test_agent_state_with_optional_fields():
    """Test AgentState with optional fields"""
    state = AgentState(
        user_message="Test",
        conversation_history=[],
        user_intent="legal_consultation",
        retrieved_context=[{"text": "context"}],
        context_str="Some context",
        sources=[{"title": "Source 1"}],
        response="A response",
        error=""
    )
    assert state["retrieved_context"][0]["text"] == "context"
    assert state["context_str"] == "Some context"
    assert state["response"] == "A response"
