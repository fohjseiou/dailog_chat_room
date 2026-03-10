"""Agent state definition for LangGraph workflow."""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """State for the legal consultation agent workflow."""

    # Required fields
    user_message: str
    conversation_history: List[Dict[str, str]]
    user_intent: str

    # Optional fields
    retrieved_context: Optional[List[Dict[str, Any]]]
    context_str: Optional[str]
    sources: Optional[List[Dict[str, Any]]]
    response: Optional[str]
    error: Optional[str]


def create_initial_state(
    user_message: str,
    conversation_history: List[Dict[str, str]]
) -> AgentState:
    """Create initial state for agent workflow"""
    return {
        "user_message": user_message,
        "conversation_history": conversation_history,
        "user_intent": "",
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": None
    }
