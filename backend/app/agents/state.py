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
