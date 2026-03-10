"""End-to-end integration tests for LangChain migration.

These tests verify that all LangChain components work together correctly.
They make actual LLM calls and require valid API keys.
"""

import pytest
from app.services.llm_service import get_llm_service
from app.agents.graph import get_agent_graph, get_streaming_agent_graph
from app.agents.state import create_initial_state


@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test complete agent workflow with LangChain components."""
    # Get the compiled graph
    graph = get_agent_graph()

    # Create initial state using helper function
    initial_state = create_initial_state(
        user_message="什么是合同？",
        conversation_history=[]
    )

    # Run the graph
    result = await graph.ainvoke(initial_state)

    # Verify result
    assert result["response"] is not None
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
    assert result.get("error") in ("", None)

    # Verify intent was classified
    assert result["user_intent"] in ("greeting", "legal_consultation", "general_chat")
    assert result["user_intent"] == "legal_consultation"  # Should detect legal intent

    # If legal consultation, should have RAG context
    if result["user_intent"] == "legal_consultation":
        assert "retrieved_context" in result
        assert "sources" in result


@pytest.mark.asyncio
async def test_streaming_agent_workflow():
    """Test streaming agent workflow with LangChain components."""
    graph = get_streaming_agent_graph()

    initial_state = create_initial_state(
        user_message="你好",
        conversation_history=[]
    )

    events = []
    async for event in graph.astream(initial_state):
        events.append(event)
        # Should get events for each node

    # Verify we got events
    assert len(events) > 0

    # Track all events and tokens
    all_events = []
    final_response = None
    detected_intent = None

    for event in events:
        for node_name, node_output in event.items():
            all_events.append({"node": node_name, "output": node_output})

            # Capture intent from router
            if node_name == "intent_router":
                if isinstance(node_output, dict):
                    detected_intent = node_output.get("user_intent")

            # For streaming response generator, we get individual yields
            if node_name == "response_generator_stream":
                # The streaming node yields multiple events
                if isinstance(node_output, dict):
                    # Check for different event types
                    if "event" in node_output:
                        event_type = node_output["event"]
                        data = node_output.get("data", {})

                        if event_type == "start":
                            assert "intent" in data
                        elif event_type == "token":
                            assert "chunk" in data
                            assert "full_response" in data
                        elif event_type == "end":
                            final_response = data.get("response")
                        elif event_type == "error":
                            pytest.fail(f"Got error event: {data}")

    # Basic check that something was processed
    assert len(all_events) > 0
    assert detected_intent is not None
    assert detected_intent == "greeting"  # "你好" should be detected as greeting


@pytest.mark.asyncio
async def test_agent_workflow_with_conversation_history():
    """Test agent workflow with conversation history."""
    graph = get_agent_graph()

    # Create a conversation history
    conversation_history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！我是法律咨询助手，有什么可以帮助您的吗？"}
    ]

    initial_state = create_initial_state(
        user_message="合同有哪些类型？",
        conversation_history=conversation_history
    )

    # Run the graph
    result = await graph.ainvoke(initial_state)

    # Verify result
    assert result["response"] is not None
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
    assert result.get("error") in ("", None)

    # Should detect legal consultation intent
    assert result["user_intent"] == "legal_consultation"


@pytest.mark.asyncio
async def test_streaming_node_directly():
    """Test streaming node directly (mimics how API actually uses it)."""
    from app.agents.nodes import (
        intent_router_node,
        rag_retriever_node,
        response_generator_node_stream
    )

    # Create initial state
    state = create_initial_state(
        user_message="什么是侵权责任？",
        conversation_history=[]
    )

    # Step 1: Intent routing
    intent_result = await intent_router_node(state)
    intent = intent_result.get("user_intent", "unknown")
    state.update(intent_result)

    # Step 2: RAG retrieval if needed
    sources = []
    if intent == "legal_consultation":
        rag_result = await rag_retriever_node(state)
        state.update(rag_result)
        sources = rag_result.get("sources", [])

    # Step 3: Stream response
    events_received = []
    full_response = ""
    async for chunk_event in response_generator_node_stream(state):
        events_received.append(chunk_event)

        if chunk_event["event"] == "start":
            assert "intent" in chunk_event["data"]
        elif chunk_event["event"] == "context":
            assert "sources" in chunk_event["data"]
        elif chunk_event["event"] == "token":
            chunk = chunk_event["data"].get("chunk", "")
            full_response += chunk
        elif chunk_event["event"] == "end":
            assert "response" in chunk_event["data"]
            full_response = chunk_event["data"].get("response", "")
        elif chunk_event["event"] == "error":
            pytest.fail(f"Got error event: {chunk_event}")

    # Verify streaming completed successfully
    assert len(events_received) > 0
    assert full_response is not None
    assert len(full_response) > 0


@pytest.mark.asyncio
async def test_llm_service_directly():
    """Test LLM service directly to ensure LangChain integration works."""
    llm_service = get_llm_service()

    # Test basic response generation
    response = await llm_service.generate_response(
        message="你好",
        conversation_history=[]
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_llm_service_streaming():
    """Test LLM service streaming to ensure LangChain integration works."""
    llm_service = get_llm_service()

    # Test streaming response generation
    chunks = []
    async for chunk in llm_service.generate_response_stream(
        message="你好",
        conversation_history=[]
    ):
        chunks.append(chunk)

    # Verify we got chunks
    assert len(chunks) > 0

    # Combine chunks and verify
    full_response = "".join(chunks)
    assert len(full_response) > 0
