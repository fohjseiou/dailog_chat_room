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
    user_id: Optional[str]  # Track user for memory

    # LangGraph orchestration fields
    streaming: Optional[bool]  # Control parameter for streaming mode
    session_id: Optional[str]  # For memory extraction
    memory_extracted: Optional[bool]  # Memory extraction result
    facts_extracted: Optional[List[str]]  # Extracted facts
    summary_generated: Optional[str]  # Generated summary


def create_initial_state(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    streaming: bool = False
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
        "error": None,
        "user_id": user_id,
        "streaming": streaming,
        "session_id": session_id,
        "memory_extracted": None,
        "facts_extracted": None,
        "summary_generated": None
    }
