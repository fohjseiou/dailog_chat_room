from langgraph.graph import StateGraph, END
from typing import AsyncIterator
from app.agents.state import AgentState
from app.agents.nodes import intent_router_node, rag_retriever_node, response_generator_node, response_generator_node_stream
import logging

logger = logging.getLogger(__name__)


def create_agent_graph() -> StateGraph:
    """Create the LangGraph agent workflow"""

    # Create the graph with our state
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("rag_retriever", rag_retriever_node)
    workflow.add_node("response_generator", response_generator_node)

    # Define conditional edges from intent router
    def route_after_intent(state: AgentState) -> str:
        intent = state.get("user_intent")

        if intent == "greeting":
            # Skip RAG, go directly to response
            return "response_generator"
        elif intent == "legal_consultation":
            # Go through RAG
            return "rag_retriever"
        else:
            # General chat, skip RAG
            return "response_generator"

    # Define edges
    workflow.set_entry_point("intent_router")
    workflow.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "greeting": "response_generator",
            "legal_consultation": "rag_retriever",
            "general_chat": "response_generator"
        }
    )

    # RAG always goes to response
    workflow.add_edge("rag_retriever", "response_generator")
    workflow.add_edge("response_generator", END)

    return workflow


# Singleton
_agent_graph = None
_compiled_agent_graph = None


def get_agent_graph():
    """Get or create the compiled agent graph"""
    global _agent_graph, _compiled_agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
        _compiled_agent_graph = _agent_graph.compile()
    return _compiled_agent_graph


def create_streaming_agent_graph() -> StateGraph:
    """Create a LangGraph agent workflow for streaming responses"""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("rag_retriever", rag_retriever_node)
    workflow.add_node("response_generator_stream", response_generator_node_stream)

    # Define conditional edges from intent router
    def route_after_intent(state: AgentState) -> str:
        intent = state.get("user_intent")

        if intent == "greeting":
            return "response_generator_stream"
        elif intent == "legal_consultation":
            return "rag_retriever"
        else:
            return "response_generator_stream"

    # Define edges
    workflow.set_entry_point("intent_router")
    workflow.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "greeting": "response_generator_stream",
            "legal_consultation": "rag_retriever",
            "general_chat": "response_generator_stream"
        }
    )

    # RAG always goes to response
    workflow.add_edge("rag_retriever", "response_generator_stream")
    workflow.add_edge("response_generator_stream", END)

    return workflow


# Singleton for streaming graph
_streaming_agent_graph = None
_compiled_streaming_agent_graph = None


def get_streaming_agent_graph():
    """Get or create the compiled streaming agent graph"""
    global _streaming_agent_graph, _compiled_streaming_agent_graph
    if _streaming_agent_graph is None:
        _streaming_agent_graph = create_streaming_agent_graph()
        _compiled_streaming_agent_graph = _streaming_agent_graph.compile()
    return _compiled_streaming_agent_graph
