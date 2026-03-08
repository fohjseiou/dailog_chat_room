from typing import TypedDict, List, Dict, Any

# Define the state for our agent graph
class AgentState(TypedDict):
    """State for the legal consultation agent"""
    session_id: str
    user_message: str
    conversation_history: List[Dict[str, str]]
    user_intent: str
    retrieved_context: List[Dict[str, Any]]
    context_str: str
    sources: List[Dict[str, Any]]
    response: str
    error: str


def create_initial_state(
    session_id: str,
    user_message: str,
    conversation_history: List[Dict[str, str]]
) -> AgentState:
    """Create initial state for agent workflow"""
    return {
        "session_id": session_id,
        "user_message": user_message,
        "conversation_history": conversation_history,
        "user_intent": "",
        "retrieved_context": [],
        "context_str": "",
        "sources": [],
        "response": "",
        "error": ""
    }
