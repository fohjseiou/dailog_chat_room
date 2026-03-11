# LangGraph 编排重构实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将手动节点执行重构为 LangGraph 真正的编排 (ainvoke/astream)，支持轻松添加新 Agent

**架构:** 统一 Graph 定义，通过 state["streaming"] 控制流式/非流式模式，记忆提取作为独立后处理节点

**Tech Stack:** LangGraph 1.0.10, LangChain 0.3.20, FastAPI 0.134.0, pytest 8.4.0

---

## 文件结构

```
backend/app/agents/
├── state.py          # 更新：添加 streaming, session_id 等字段
├── nodes.py          # 更新：添加 memory_extraction_node，重构 response_generator_node
├── graph.py          # 重构：统一 Graph 定义，移除旧的流式专用 Graph
└── utils.py          # 保持不变

backend/app/api/v1/
└── chat.py           # 简化：使用 ainvoke/astream，移除手动节点调用

backend/tests/agents/
├── test_graph_execution.py       # 新增：Graph 执行测试
├── test_nodes_memory_integration.py  # 更新：适配新的 memory_extraction_node
└── test_streaming.py             # 更新：适配新的流式处理
```

---

## Chunk 1: 更新 State 定义

### Task 1: 更新 AgentState 添加新字段

**Files:**
- Modify: `backend/app/agents/state.py`

- [ ] **Step 1: 备份当前 state.py**

```bash
cp backend/app/agents/state.py backend/app/agents/state.py.backup
```

- [ ] **Step 2: 读取当前 state.py 内容**

当前内容应包含：
```python
class AgentState(TypedDict):
    user_message: str
    conversation_history: List[Dict[str, str]]
    user_intent: str
    retrieved_context: Optional[List[Dict[str, Any]]]
    context_str: Optional[str]
    sources: Optional[List[Dict[str, Any]]]
    response: Optional[str]
    error: Optional[str]
    user_id: Optional[str]
```

- [ ] **Step 3: 更新 AgentState 添加新字段**

```python
class AgentState(TypedDict):
    """State for the agent workflow"""

    # 输入
    user_message: str
    conversation_history: List[Dict[str, str]]

    # 控制参数
    streaming: bool  # 新增：是否启用流式模式
    user_id: Optional[str]
    session_id: Optional[str]  # 新增：用于记忆提取

    # 流程状态
    user_intent: str

    # RAG 相关
    retrieved_context: Optional[List[Dict[str, Any]]]
    context_str: Optional[str]
    sources: Optional[List[Dict[str, Any]]]

    # 输出
    response: Optional[str]
    error: Optional[str]

    # 记忆相关（新增）
    memory_extracted: Optional[bool]
    facts_extracted: Optional[List[str]]
    summary_generated: Optional[str]
```

- [ ] **Step 4: 更新 create_initial_state 函数**

```python
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
        "streaming": streaming,
        "user_id": user_id,
        "session_id": session_id,
        "user_intent": "",
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": None,
        "memory_extracted": None,
        "facts_extracted": None,
        "summary_generated": None
    }
```

- [ ] **Step 5: 运行现有测试验证兼容性**

```bash
cd backend
pytest tests/agents/ -v
```

Expected: 所有测试通过（新字段有默认值）

- [ ] **Step 6: 提交变更**

```bash
git add backend/app/agents/state.py
git commit -m "refactor(state): add streaming, session_id and memory fields to AgentState"
```

---

## Chunk 2: 添加 memory_extraction_node

### Task 2: 实现记忆提取节点

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: 在 nodes.py 顶部添加必要导入**

检查以下导入存在：
```python
from typing import Dict, Any, AsyncIterator, Optional, List
from app.services.memory_extraction_service import MemoryExtractionService
from app.services.session_service import SessionService
```

- [ ] **Step 2: 添加 memory_extraction_node 函数**

在 `response_generator_node_stream` 函数后添加：

```python
async def memory_extraction_node(state: AgentState) -> Dict[str, Any]:
    """
    Extract and store long-term memories from conversation.

    This node is only executed for authenticated users (when user_id is present).
    It extracts user facts and generates conversation summaries.

    Args:
        state: Current agent state containing user_id, session_id, and conversation history

    Returns:
        Dict with memory extraction results
    """
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    conversation_history = state.get("conversation_history", [])
    user_message = state.get("user_message", "")

    # Skip if not authenticated
    if not user_id:
        return {
            "memory_extracted": False,
            "facts_extracted": [],
            "summary_generated": None
        }

    try:
        # Import here to avoid circular dependency
        from app.database import get_db

        # Get database session
        async for db in get_db():
            try:
                extraction_service = MemoryExtractionService(db)
                session_service = SessionService(db)

                # Get message count
                session = await session_service.get_session(session_id)
                message_count = session.message_count if session else 0

                # Build last N messages for context
                last_n_messages = conversation_history[-5:] if conversation_history else []
                last_n_messages.append({"role": "user", "content": user_message})

                # Extract memories
                results = await extraction_service.process_conversation_memory(
                    user_id=user_id,
                    session_id=session_id,
                    message_count=message_count,
                    last_user_message=user_message,
                    last_n_messages=last_n_messages
                )

                return {
                    "memory_extracted": True,
                    "facts_extracted": results.get("facts_extracted", []),
                    "summary_generated": results.get("summary_generated")
                }
            finally:
                pass
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in memory_extraction_node: {e}")
        return {
            "memory_extracted": False,
            "facts_extracted": [],
            "summary_generated": None
        }
```

- [ ] **Step 3: 添加 memory_extraction_node 单元测试**

创建文件 `backend/tests/agents/test_memory_extraction_node.py`:

```python
"""Tests for memory_extraction_node"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from app.agents.nodes import memory_extraction_node
from app.agents.state import create_initial_state


@pytest.mark.asyncio
async def test_memory_extraction_skipped_for_anonymous_user(db_session):
    """Test that memory extraction is skipped for anonymous users"""
    state = create_initial_state(
        user_message="Test message",
        conversation_history=[],
        user_id=None,  # Anonymous
        session_id="test-session"
    )

    result = await memory_extraction_node(state)

    assert result["memory_extracted"] is False
    assert result["facts_extracted"] == []


@pytest.mark.asyncio
async def test_memory_extraction_executes_for_authenticated_user(db_session):
    """Test that memory extraction executes for authenticated users"""
    user_id = "test-user-123"
    session_id = "test-session-456"

    state = create_initial_state(
        user_message="我是律师，专精合同法",
        conversation_history=[
            {"role": "assistant", "content": "您好，有什么可以帮助您的？"}
        ],
        user_id=user_id,
        session_id=session_id
    )

    # Mock the services
    with patch('app.agents.nodes.MemoryExtractionService') as MockMemoryExtraction:
        mock_service = AsyncMock()
        mock_service.process_conversation_memory = AsyncMock(return_value={
            "facts_extracted": ["用户是执业律师"],
            "summary_generated": "讨论合同法相关问题"
        })
        MockMemoryExtraction.return_value = mock_service

        with patch('app.agents.nodes.SessionService') as MockSessionService:
            mock_session_service = AsyncMock()
            mock_session = Mock()
            mock_session.message_count = 5
            mock_session_service.get_session = AsyncMock(return_value=mock_session)
            MockSessionService.return_value = mock_session_service

            result = await memory_extraction_node(state)

    assert result["memory_extracted"] is True
    assert len(result["facts_extracted"]) > 0
    assert result["summary_generated"] is not None


@pytest.mark.asyncio
async def test_memory_extraction_handles_errors_gracefully(db_session):
    """Test that memory extraction handles errors gracefully"""
    state = create_initial_state(
        user_message="Test",
        conversation_history=[],
        user_id="test-user",
        session_id="test-session"
    )

    # Mock to raise error
    with patch('app.agents.nodes.get_db') as mock_get_db:
        mock_get_db.side_effect = Exception("Database error")

        result = await memory_extraction_node(state)

    assert result["memory_extracted"] is False
```

- [ ] **Step 4: 运行测试**

```bash
cd backend
pytest tests/agents/test_memory_extraction_node.py -v
```

Expected: 所有测试通过

- [ ] **Step 5: 提交变更**

```bash
git add backend/app/agents/nodes.py backend/tests/agents/test_memory_extraction_node.py
git commit -m "feat(nodes): add memory_extraction_node for long-term memory extraction"
```

---

## Chunk 3: 重构 Graph 定义

### Task 3: 创建统一的 Agent Graph

**Files:**
- Modify: `backend/app/agents/graph.py`

- [ ] **Step 1: 备份当前 graph.py**

```bash
cp backend/app/agents/graph.py backend/app/agents/graph.py.backup
```

- [ ] **Step 2: 重写 graph.py**

完全替换为以下内容：

```python
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
        START → intent_router → [rag_retriever?] → response_generator
                                                         ↓
                                            [authenticated?] → memory_extraction
                                                         ↓
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
```

- [ ] **Step 3: 添加 Graph 执行测试**

创建文件 `backend/tests/agents/test_graph_execution.py`:

```python
"""Tests for unified agent graph execution"""
import pytest
from app.agents.graph import get_unified_agent_graph
from app.agents.state import create_initial_state


@pytest.mark.asyncio
async def test_graph_legal_consultation_flow(db_session):
    """Test graph execution for legal consultation intent"""
    graph = get_unified_agent_graph()

    state = create_initial_state(
        user_message="合同违约怎么赔偿？",
        conversation_history=[],
        streaming=False
    )

    # Mock the nodes to avoid actual LLM calls
    from unittest.mock import patch, AsyncMock

    with patch('app.agents.nodes.intent_router_node') as mock_intent:
        mock_intent.return_value = {"user_intent": "legal_consultation"}

    with patch('app.agents.nodes.rag_retriever_node') as mock_rag:
        mock_rag.return_value = {
            "retrieved_context": [{"text": "合同法相关规定"}],
            "context_str": "合同法第XX条",
            "sources": [{"title": "合同法"}]
        }

    with patch('app.agents.nodes.response_generator_node') as mock_response:
        mock_response.return_value = {"response": "根据合同法..."}

    result = await graph.ainvoke(state)

    assert "response" in result
    # Verify nodes were called in correct order
    mock_intent.assert_called_once()
    mock_rag.assert_called_once()
    mock_response.assert_called_once()


@pytest.mark.asyncio
async def test_graph_greeting_flow(db_session):
    """Test graph execution for greeting intent (skips RAG)"""
    graph = get_unified_agent_graph()

    state = create_initial_state(
        user_message="你好",
        conversation_history=[],
        streaming=False
    )

    from unittest.mock import patch, AsyncMock

    with patch('app.agents.nodes.intent_router_node') as mock_intent:
        mock_intent.return_value = {"user_intent": "greeting"}

    with patch('app.agents.nodes.response_generator_node') as mock_response:
        mock_response.return_value = {"response": "您好！"}

    result = await graph.ainvoke(state)

    assert result["response"] == "您好！"
    mock_intent.assert_called_once()
    mock_response.assert_called_once()


@pytest.mark.asyncio
async def test_graph_memory_extraction_for_authenticated_user(db_session):
    """Test that memory extraction is triggered for authenticated users"""
    graph = get_unified_agent_graph()

    state = create_initial_state(
        user_message="测试",
        conversation_history=[],
        user_id="test-user-123",
        session_id="test-session",
        streaming=False
    )

    from unittest.mock import patch

    with patch('app.agents.nodes.intent_router_node') as mock_intent:
        mock_intent.return_value = {"user_intent": "general_chat"}

    with patch('app.agents.nodes.response_generator_node') as mock_response:
        mock_response.return_value = {"response": "回复"}

    with patch('app.agents.nodes.memory_extraction_node') as mock_memory:
        mock_memory.return_value = {"memory_extracted": True}

    result = await graph.ainvoke(state)

    # Memory extraction should be called for authenticated users
    mock_memory.assert_called_once()


@pytest.mark.asyncio
async def test_graph_skips_memory_for_anonymous_user(db_session):
    """Test that memory extraction is skipped for anonymous users"""
    graph = get_unified_agent_graph()

    state = create_initial_state(
        user_message="测试",
        conversation_history=[],
        user_id=None,  # Anonymous
        streaming=False
    )

    from unittest.mock import patch

    with patch('app.agents.nodes.intent_router_node') as mock_intent:
        mock_intent.return_value = {"user_intent": "general_chat"}

    with patch('app.agents.nodes.response_generator_node') as mock_response:
        mock_response.return_value = {"response": "回复"}

    with patch('app.agents.nodes.memory_extraction_node') as mock_memory:
        mock_memory.return_value = {"memory_extracted": False}

    result = await graph.ainvoke(state)

    # Memory extraction should still be called but returns early
    # The routing should skip it for anonymous users
    assert "memory_extracted" not in result or result.get("memory_extracted") is False


@pytest.mark.asyncio
async def test_graph_streaming_mode(db_session):
    """Test graph execution in streaming mode"""
    graph = get_unified_agent_graph()

    state = create_initial_state(
        user_message="你好",
        conversation_history=[],
        streaming=True
    )

    from unittest.mock import patch, AsyncMock

    with patch('app.agents.nodes.intent_router_node') as mock_intent:
        mock_intent.return_value = {"user_intent": "greeting"}

    with patch('app.agents.nodes.response_generator_node') as mock_response:
        mock_response.return_value = {"response": "您好！"}

    # Collect all events from streaming
    events = []
    async for event in graph.astream(state):
        events.append(event)

    # Should have events for each node
    assert len(events) > 0
```

- [ ] **Step 4: 运行测试**

```bash
cd backend
pytest tests/agents/test_graph_execution.py -v
```

Expected: 所有测试通过

- [ ] **Step 5: 运行所有 agent 测试确保兼容性**

```bash
cd backend
pytest tests/agents/ -v
```

Expected: 所有测试通过

- [ ] **Step 6: 提交变更**

```bash
git add backend/app/agents/graph.py backend/tests/agents/test_graph_execution.py
git commit -m "refactor(graph): create unified agent graph with ainvoke/astream support"
```

---

## Chunk 4: 重构 chat.py API 层

### Task 4: 简化非流式接口

**Files:**
- Modify: `backend/app/api/v1/chat.py`

- [ ] **Step 1: 备份当前 chat.py**

```bash
cp backend/app/api/v1/chat.py backend/app/api/v1/chat.py.backup
```

- [ ] **Step 2: 更新导入**

将导入行更新为：

```python
from app.agents.graph import get_unified_agent_graph
from app.agents.state import create_initial_state
```

移除不再需要的导入：
```python
# Remove these:
# from app.agents.nodes import intent_router_node, rag_retriever_node, response_generator_node
```

- [ ] **Step 3: 重写 chat 函数**

替换现有的 `@router.post("")` chat 函数：

```python
@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send a message and get a response from the agent system.

    Uses LangGraph ainvoke for execution.
    """
    session_service = SessionService(db)
    message_service = MessageService(db)

    # Get user_id from authenticated user, or None for anonymous
    user_id = current_user.id if current_user else None

    # Prepare session and history
    session_id, conversation_history = await _prepare_session(
        session_service, message_service, request, user_id
    )

    try:
        # Create initial state
        state = create_initial_state(
            user_message=request.message,
            conversation_history=conversation_history,
            user_id=user_id,
            session_id=session_id,
            streaming=False
        )

        # Execute graph using ainvoke
        agent_graph = get_unified_agent_graph()
        final_state = await agent_graph.ainvoke(state)

        # Extract response
        response_content = final_state.get("response", "")
        sources = final_state.get("sources", [])

        # Handle error if any
        if final_state.get("error"):
            logger.error(f"Agent error: {final_state['error']}")

        # Save the exchange
        await message_service.save_exchange(
            session_id,
            request.message,
            response_content,
            {
                "type": "agent_response",
                "model": "qwen-langgraph",
                "sources": sources,
                "intent": final_state.get("user_intent", "unknown")
            }
        )

        # Update session
        await session_service.increment_message_count(session_id)

        return {
            "session_id": session_id,
            "response": response_content,
            "sources": sources
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")
```

- [ ] **Step 4: 添加辅助函数 _prepare_session**

在文件中 `_format_sse` 函数前添加：

```python
async def _prepare_session(
    session_service: SessionService,
    message_service: MessageService,
    request: ChatRequest,
    user_id: Optional[str]
) -> tuple[str, list[Dict]]:
    """
    Prepare session and conversation history.

    Returns:
        tuple of (session_id, conversation_history)
    """
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = await message_service.get_messages_by_session(request.session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-10:]  # Limit to last 10 messages
        ]
        return request.session_id, conversation_history
    else:
        new_session = await session_service.create_session({"title": None}, user_id=user_id)
        return new_session.id, []
```

- [ ] **Step 5: 移除不再需要的 _extract_conversation_memory 函数**

这个函数现在由 Graph 中的 memory_extraction_node 处理。

删除以下代码块：
```python
# Remove this entire function:
async def _extract_conversation_memory(...)
```

- [ ] **Step 6: 更新非流式接口测试**

更新 `backend/tests/api/test_chat_api_user_id.py` 中的测试：

```python
@pytest.mark.asyncio
async def test_chat_with_authenticated_user_uses_graph(client, authenticated_user):
    """Test that chat endpoint uses LangGraph for authenticated users"""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "合同违约怎么办？"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "response" in data
    assert "session_id" in data
    assert data["session_id"] is not None
```

- [ ] **Step 7: 运行测试**

```bash
cd backend
pytest tests/api/test_chat_api_user_id.py -v
```

Expected: 测试通过

- [ ] **Step 8: 提交变更**

```bash
git add backend/app/api/v1/chat.py backend/tests/api/test_chat_api_user_id.py
git commit -m "refactor(api): use graph.ainvoke for non-streaming chat endpoint"
```

---

### Task 5: 重构流式接口

**Files:**
- Modify: `backend/app/api/v1/chat.py`

- [ ] **Step 1: 重写 chat_stream 函数**

```python
@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> StreamingResponse:
    """
    Send a message and get a streaming response via Server-Sent Events.

    Uses LangGraph astream for execution.

    SSE Events:
    - session_id: Initial session ID
    - intent: User's intent classification
    - context: Retrieved knowledge base context
    - token: Response text chunk
    - end: Response completed
    - error: Error occurred
    """
    return StreamingResponse(
        _stream_chat_events(request, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

- [ ] **Step 2: 重写 _stream_chat_events 函数**

完全替换现有实现：

```python
async def _stream_chat_events(
    request: ChatRequest,
    db: AsyncSession,
    current_user: Optional[User] = None
) -> AsyncIterator[str]:
    """
    Generate SSE events for streaming chat using graph.astream().

    Yields SSE-formatted events for each node execution.
    """
    session_service = SessionService(db)
    message_service = MessageService(db)

    user_id = current_user.id if current_user else None

    # Prepare session and history
    session_id, conversation_history = await _prepare_session(
        session_service, message_service, request, user_id
    )

    # Send session_id first
    yield _format_sse("session_id", {"session_id": session_id})

    # Create initial state with streaming=True
    state = create_initial_state(
        user_message=request.message,
        conversation_history=conversation_history,
        user_id=user_id,
        session_id=session_id,
        streaming=True
    )

    try:
        # Execute graph using astream
        agent_graph = get_unified_agent_graph()

        full_response = ""
        sources = []
        intent = "unknown"

        # Process streaming events from graph
        async for event in agent_graph.astream(state):
            # event format: {"node_name": {output_dict}}
            for node_name, node_output in event.items():

                # Intent routing completed
                if node_name == "intent_router":
                    intent = node_output.get("user_intent", "unknown")
                    yield _format_sse("intent", {"intent": intent})

                # RAG retrieval completed
                elif node_name == "rag_retriever":
                    sources = node_output.get("sources", [])
                    if sources:
                        yield _format_sse("context", {"sources": sources})

                # Response generation - handle streaming chunks
                elif node_name == "response_generator":
                    # Check if streaming output is available
                    if "streaming_chunk" in node_output:
                        chunk = node_output["streaming_chunk"]
                        full_response += chunk
                        yield _format_sse("token", {
                            "chunk": chunk,
                            "full_response": full_response
                        })
                    # Non-streaming fallback
                    elif "response" in node_output:
                        full_response = node_output["response"]

                # Memory extraction completed (silent)
                elif node_name == "memory_extraction":
                    if node_output.get("memory_extracted"):
                        logger.info(f"Memory extraction completed for session {session_id}")

        # Send end event
        yield _format_sse("end", {"response": full_response})

        # Save conversation after streaming completes
        if full_response:
            await message_service.save_exchange(
                session_id,
                request.message,
                full_response,
                {
                    "type": "agent_response_stream",
                    "model": "qwen-langgraph-stream",
                    "sources": sources,
                    "intent": intent
                }
            )

            # Update session message count
            await session_service.increment_message_count(session_id)

    except Exception as e:
        logger.error(f"Error in stream chat endpoint: {e}", exc_info=True)
        yield _format_sse("error", {"error": str(e)})
```

- [ ] **Step 3: 更新流式接口测试**

更新 `backend/tests/test_streaming.py`：

```python
"""Tests for streaming chat using LangGraph astream"""
import pytest
import json
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_stream_chat_uses_graph_astream(client: AsyncClient):
    """Test that streaming chat uses graph.astream()"""
    async with client.stream("POST", "/api/v1/chat/stream", json={
        "message": "你好"
    }) as response:
        assert response.status_code == 200

        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                events.append(data)

        # Should have session_id, intent, and end events
        event_types = [e.get("event") for e in events]
        assert "session_id" in event_types or any("session_id" in str(e) for e in events)


@pytest.mark.asyncio
async def test_stream_chat_sends_intent_event(client: AsyncClient):
    """Test that intent classification is sent as SSE event"""
    async with client.stream("POST", "/api/v1/chat/stream", json={
        "message": "合同违约怎么办？"
    }) as response:
        intent_found = False
        async for line in response.aiter_lines():
            if "intent" in line.lower():
                intent_found = True
                break

        assert intent_found
```

- [ ] **Step 4: 运行测试**

```bash
cd backend
pytest tests/test_streaming.py -v
```

Expected: 测试通过

- [ ] **Step 5: 运行完整测试套件**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: 所有测试通过

- [ ] **Step 6: 提交变更**

```bash
git add backend/app/api/v1/chat.py backend/tests/test_streaming.py
git commit -m "refactor(api): use graph.astream for streaming chat endpoint"
```

---

## Chunk 5: 验证和清理

### Task 6: 端到端验证

- [ ] **Step 1: 启动后端服务**

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: 测试非流式接口**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

Expected: 返回 JSON 响应，包含 `response` 和 `session_id`

- [ ] **Step 3: 测试流式接口**

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

Expected: 返回 SSE 流，包含多个事件

- [ ] **Step 4: 测试法律咨询意图**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "合同违约怎么赔偿？"}'
```

Expected: 返回带 `sources` 的响应

- [ ] **Step 5: 清理备份文件**

```bash
rm backend/app/agents/*.backup
rm backend/app/api/v1/*.backup
```

- [ ] **Step 6: 最终提交**

```bash
git add backend/
git commit -m "chore: cleanup backup files after LangGraph refactor"
```

---

## 扩展验证（可选）

### Task 7: 添加示例 Agent 验证扩展性

此任务验证添加新 Agent 的简易性。

**Files:**
- Modify: `backend/app/agents/nodes.py`
- Modify: `backend/app/agents/graph.py`

- [ ] **Step 1: 添加文档分析意图到 intent_router_node**

在 `nodes.py` 的 `intent_router_node` 函数中添加：

```python
# Add to existing keywords
doc_keywords = ["文档", "文件", "分析", "pdf", "docx"]

# Add to intent check
if any(kw in message for kw in doc_keywords):
    return {"user_intent": "document_analysis"}
```

- [ ] **Step 2: 添加简单的 doc_analyzer_node**

```python
async def doc_analyzer_node(state: AgentState) -> Dict[str, Any]:
    """
    Document analysis node (placeholder for future implementation).

    Currently returns a simple response indicating document analysis
    would be performed here.
    """
    user_message = state.get("user_message", "")

    return {
        "doc_analysis": f"文档分析请求: {user_message}",
        "context_str": "文档分析功能即将推出",
        "sources": [{"type": "document", "message": "示例文档源"}]
    }
```

- [ ] **Step 3: 更新 graph.py**

在 `create_unified_agent_graph` 函数中：

```python
# Add node
workflow.add_node("doc_analyzer", doc_analyzer_node)

# Update route_after_intent
def route_after_intent(state: AgentState) -> str:
    intent = state.get("user_intent")

    if intent == "legal_consultation":
        return "rag_retriever"
    elif intent == "document_analysis":
        return "doc_analyzer"
    else:
        return "response_generator"

# Add edge
workflow.add_conditional_edges(
    "intent_router",
    route_after_intent,
    {
        "rag_retriever": "rag_retriever",
        "doc_analyzer": "doc_analyzer",
        "response_generator": "response_generator"
    }
)

workflow.add_edge("doc_analyzer", "response_generator")
```

- [ ] **Step 4: 测试新 Agent**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我分析这个文档"}'
```

Expected: 返回包含文档分析信息的响应

- [ ] **Step 5: 提交扩展性验证代码**

```bash
git add backend/app/agents/nodes.py backend/app/agents/graph.py
git commit -m "test: add document_analysis agent to verify extensibility"
```

- [ ] **Step 6: 清理验证代码（可选）**

如果不想保留这个示例 Agent：

```bash
git revert HEAD
```

---

## 完成清单

- [ ] State 定义已更新
- [ ] memory_extraction_node 已实现并测试
- [ ] Graph 定义已重构为统一版本
- [ ] 非流式接口使用 ainvoke
- [ ] 流式接口使用 astream
- [ ] 所有测试通过
- [ ] 手动测试验证
- [ ] 扩展性验证（添加示例 Agent）
- [ ] 文档已更新

---

## 回滚计划

如果需要回滚：

```bash
# 查看提交历史
git log --oneline

# 回滚到重构前的状态
git revert <commit-hash>

# 或者使用备份文件恢复
cp backend/app/agents/state.py.backup backend/app/agents/state.py
cp backend/app/agents/graph.py.backup backend/app/agents/graph.py
cp backend/app/api/v1/chat.py.backup backend/app/api/v1/chat.py
```
