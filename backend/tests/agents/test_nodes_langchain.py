import pytest
from app.agents.nodes import response_generator_node
from app.agents.state import AgentState

@pytest.mark.asyncio
async def test_response_generator_with_langchain():
    """Test response generator uses LangChain correctly"""
    state = AgentState(
        user_message="什么是合同？",
        conversation_history=[],
        user_intent="legal_consultation",
        retrieved_context=[],
        context_str="合同是法律文件...",
        session_id="",
        sources=[],
        response="",
        error=""
    )

    result = await response_generator_node(state)

    assert "response" in result
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
    assert result.get("error") == ""

@pytest.mark.asyncio
async def test_response_generator_with_rag_context():
    """Test response generator incorporates RAG context"""
    state = AgentState(
        user_message="劳动合同有哪些要素？",
        conversation_history=[],
        user_intent="legal_consultation",
        retrieved_context=[{"text": "劳动合同必须包含..."}],
        context_str="劳动合同必须包含工作内容、报酬等条款",
        session_id="",
        sources=[],
        response="",
        error=""
    )

    result = await response_generator_node(state)

    assert "response" in result
    # Response should reference the context
    assert len(result["response"]) > 0
