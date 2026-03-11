"""LangGraph agent workflow for legal consultation system.

This module defines a unified agent graph that handles both streaming
and non-streaming responses through a single workflow definition.
"""
from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.nodes import (
    intent_router_node,
    rag_retriever_node,
    response_generator_node,
    memory_extraction_node
)
import logging

logger = logging.getLogger(__name__)


def create_unified_agent_graph() -> StateGraph:
    """
    Create the unified LangGraph agent workflow.

    This graph supports both streaming and non-streaming modes through
    the state['streaming'] configuration. The routing is determined by
    the user_intent field set by the intent_router node.

    Flow:
        START -> intent_router -> [rag_retriever?] -> response_generator
                                                         |
                                            [authenticated?] -> memory_extraction
                                                         |
                                                        END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("rag_retriever", rag_retriever_node)
    workflow.add_node("response_generator", response_generator_node)
    workflow.add_node("memory_extraction", memory_extraction_node)

    # Route after intent: decide whether to go through RAG
    def route_after_intent(state: AgentState) -> str:
        """Route to RAG or directly to response based on intent"""
        intent = state.get("user_intent")

        if intent == "legal_consultation":
            return "rag_retriever"
        else:
            # greeting, general_chat, etc. go directly to response
            return "response_generator"

    # Route after response: decide whether to extract memory
    def route_after_response(state: AgentState) -> str:
        """Route to memory extraction or END based on authentication"""
        user_id = state.get("user_id")

        if user_id:
            return "memory_extraction"
        else:
            return END

    # Define edges
    workflow.add_edge(START, "intent_router")

    workflow.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "rag_retriever": "rag_retriever",
            "response_generator": "response_generator"
        }
    )

    workflow.add_edge("rag_retriever", "response_generator")

    workflow.add_conditional_edges(
        "response_generator",
        route_after_response,
        {
            "memory_extraction": "memory_extraction",
            END: END
        }
    )

    workflow.add_edge("memory_extraction", END)

    return workflow


# Singleton pattern for graph instance
_unified_graph = None
_compiled_unified_graph = None


def get_unified_agent_graph():
    """
    Get or create the compiled unified agent graph.

    Returns:
        Compiled StateGraph ready for ainvoke() or astream() calls
    """
    global _unified_graph, _compiled_unified_graph

    if _unified_graph is None:
        _unified_graph = create_unified_agent_graph()
        _compiled_unified_graph = _unified_graph.compile()
        logger.info("Unified agent graph compiled successfully")

    return _compiled_unified_graph


# Legacy: Keep old function names for backward compatibility
def get_agent_graph():
    """Legacy alias for get_unified_agent_graph"""
    return get_unified_agent_graph()


def get_streaming_agent_graph():
    """Legacy alias for get_unified_agent_graph (streaming controlled by state)"""
    return get_unified_agent_graph()
