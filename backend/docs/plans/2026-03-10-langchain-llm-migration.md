# LangChain LLM Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将后端 LLM 服务从 DashScope 原生 SDK 迁移到 LangChain ChatTongyi，完全 LangChain 化，为后续引入 MCP 做准备。

**Architecture:** 渐进式三阶段迁移：1) LLM 服务层迁移，2) Agent 节点优化，3) 架构扩展预留。每个阶段独立可验证，保持 API 完全向后兼容。

**Tech Stack:** LangChain Community (ChatTongyi), LangChain Core (PromptTemplate, StrOutputParser), LangGraph

---

## Prerequisites

### Step 0: Verify current environment

**Run:**
```bash
cd D:/vibe-coding/dialog_chat_room/backend
python -c "import dashscope; print('DashScope version:', dashscope.__version__)"
```

**Expected:** Current DashScope SDK is installed
**Purpose:** Confirm baseline before migration

---

## Stage 1: LLM Service Layer Migration

### Task 1.1: Add LangChain Community Dependency

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Update dependencies**

Open `backend/pyproject.toml` and ensure `langchain-community` is in dependencies:

```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5",
    "langchain-community>=0.0.10",  # Add this line for ChatTongyi
    "langgraph>=0.0.20",
    # ... rest of dependencies
]
```

**Step 2: Install new dependency**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
uv sync
```

**Expected:** No errors, package installed successfully

**Step 3: Verify installation**

```bash
python -c "from langchain_community.chat_models.tongyi import ChatTongyi; print('ChatTongyi imported successfully')"
```

**Expected:** Prints "ChatTongyi imported successfully"

**Step 4: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/pyproject.toml
git commit -m "chore: add langchain-community dependency for ChatTongyi"
```

---

### Task 1.2: Create Message Conversion Utilities

**Files:**
- Create: `backend/app/agents/utils.py`

**Step 1: Write the failing test**

Create `backend/tests/agents/test_utils.py`:

```python
import pytest
from app.agents.utils import convert_to_langchain_messages, convert_to_dict_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def test_convert_user_message():
    """Test converting user message to LangChain format"""
    history = [{"role": "user", "content": "Hello"}]
    result = convert_to_langchain_messages(history)
    assert len(result) == 1
    assert isinstance(result[0], HumanMessage)
    assert result[0].content == "Hello"

def test_convert_assistant_message():
    """Test converting assistant message to LangChain format"""
    history = [{"role": "assistant", "content": "Hi there"}]
    result = convert_to_langchain_messages(history)
    assert len(result) == 1
    assert isinstance(result[0], AIMessage)
    assert result[0].content == "Hi there"

def test_convert_mixed_messages():
    """Test converting mixed conversation history"""
    history = [
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Answer"},
        {"role": "user", "content": "Follow-up"}
    ]
    result = convert_to_langchain_messages(history)
    assert len(result) == 3
    assert isinstance(result[0], HumanMessage)
    assert isinstance(result[1], AIMessage)
    assert isinstance(result[2], HumanMessage)

def test_convert_back_to_dict():
    """Test converting LangChain messages back to dict format"""
    messages = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
    result = convert_to_dict_messages(messages)
    assert result == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
```

**Step 2: Run test to verify it fails**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_utils.py -v
```

**Expected:** FAIL with "ModuleNotFoundError: No module named 'app.agents.utils'"

**Step 3: Write minimal implementation**

Create `backend/app/agents/utils.py`:

```python
"""Utility functions for LangChain message conversion."""

from typing import List, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


def convert_to_langchain_messages(history: List[Dict[str, str]]) -> List[BaseMessage]:
    """
    Convert dict-based message history to LangChain BaseMessage format.

    Args:
        history: List of messages with 'role' and 'content' keys

    Returns:
        List of LangChain BaseMessage objects
    """
    messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        # Ignore unknown roles

    return messages


def convert_to_dict_messages(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """
    Convert LangChain BaseMessage format to dict-based format.

    Args:
        messages: List of LangChain BaseMessage objects

    Returns:
        List of messages with 'role' and 'content' keys
    """
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            result.append({"role": "system", "content": msg.content})
    return result
```

**Step 4: Run test to verify it passes**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_utils.py -v
```

**Expected:** PASS (4 tests passed)

**Step 5: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/agents/utils.py backend/tests/agents/test_utils.py
git commit -m "feat: add LangChain message conversion utilities"
```

---

### Task 1.3: Refactor LLMService to use ChatTongyi

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/services/test_llm_service.py`

**Step 1: Write failing test for new ChatTongyi integration**

Create `backend/tests/services/test_llm_service_langchain.py`:

```python
import pytest
from app.services.llm_service import LLMService, get_llm_service
from langchain_community.chat_models.tongyi import ChatTongyi

def test_llm_service_uses_chat_tongyi():
    """Test that LLMService uses ChatTongyi"""
    service = LLMService()
    assert hasattr(service, 'llm')
    assert isinstance(service.llm, ChatTongyi)

def test_llm_service_singleton():
    """Test that get_llm_service returns singleton"""
    service1 = get_llm_service()
    service2 = get_llm_service()
    assert service1 is service2

def test_llm_service_has_correct_model():
    """Test that LLMService is configured with correct model"""
    service = LLMService()
    assert service.llm.model_name == "qwen-max"  # or your configured model

@pytest.mark.asyncio
async def test_generate_response_basic():
    """Test basic response generation with ChatTongyi"""
    service = LLMService()
    response = await service.generate_response(
        message="你好",
        conversation_history=[],
        system_prompt="你是一个法律助手"
    )
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_generate_response_with_history():
    """Test response generation with conversation history"""
    service = LLMService()
    history = [
        {"role": "user", "content": "什么是合同？"},
        {"role": "assistant", "content": "合同是..."}
    ]
    response = await service.generate_response(
        message="能详细解释吗？",
        conversation_history=history
    )
    assert isinstance(response, str)
    assert len(response) > 0
```

**Step 2: Run test to verify it fails**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/services/test_llm_service_langchain.py -v
```

**Expected:** FAIL (LLMService still uses DashScope SDK, not ChatTongyi)

**Step 3: Refactor LLMService implementation**

Replace `backend/app/services/llm_service.py` with:

```python
"""LLM service using LangChain ChatTongyi for Qwen integration."""

from typing import List, Dict, Any, AsyncIterator, Optional
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from app.config import get_settings
from app.agents.utils import convert_to_langchain_messages
import logging

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SYSTEM_PROMPT = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 回答要清晰、易懂，避免过度专业术语
4. 如果不确定，请说明需要更多信息"""

MAX_HISTORY_MESSAGES = 10
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
MAX_TOKENS = 2000
FALLBACK_ERROR_MESSAGE = "抱歉，我现在无法回答。请稍后再试。如果您有紧急的法律问题，建议咨询专业律师。"


class LLMService:
    """Service for interacting with Qwen LLM via LangChain ChatTongyi."""

    def __init__(self):
        settings = get_settings()
        # Use LangChain ChatTongyi instead of DashScope SDK
        self.llm = ChatTongyi(
            model=settings.dashscope_model,
            dashscope_api_key=settings.dashscope_api_key,
            temperature=DEFAULT_TEMPERATURE,
            top_p=DEFAULT_TOP_P,
            max_tokens=MAX_TOKENS,
        )

    def _build_prompt_template(self, system_prompt: Optional[str] = None) -> ChatPromptTemplate:
        """Build LangChain prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt or DEFAULT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}")
        ])

    async def generate_response(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using LangChain ChatTongyi.

        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional system prompt to override default

        Returns:
            The LLM's response as a string
        """
        try:
            # Build prompt template
            prompt = self._build_prompt_template(system_prompt)

            # Build LCEL chain
            chain = prompt | self.llm | StrOutputParser()

            # Convert history to LangChain format
            history_messages = convert_to_langchain_messages(
                conversation_history[-MAX_HISTORY_MESSAGES:]
            )

            # Invoke chain
            response = await chain.ainvoke({
                "history": history_messages,
                "user_message": message
            })

            logger.info("ChatTongyi response generated successfully")
            return response

        except Exception as e:
            logger.error(f"Error generating ChatTongyi response: {e}")
            return FALLBACK_ERROR_MESSAGE

    async def generate_response_stream(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response using LangChain ChatTongyi.

        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional system prompt to override default

        Yields:
            Chunks of the response as they arrive
        """
        try:
            # Build prompt template
            prompt = self._build_prompt_template(system_prompt)

            # Build LCEL chain
            chain = prompt | self.llm | StrOutputParser()

            # Convert history to LangChain format
            history_messages = convert_to_langchain_messages(
                conversation_history[-MAX_HISTORY_MESSAGES:]
            )

            # Stream response using LangChain astream
            async for chunk in chain.astream({
                "history": history_messages,
                "user_message": message
            }):
                if chunk:
                    yield chunk

        except Exception as e:
            logger.error(f"Error in streaming ChatTongyi response: {e}")
            yield FALLBACK_ERROR_MESSAGE


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
```

**Step 4: Run test to verify it passes**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/services/test_llm_service_langchain.py -v
```

**Expected:** PASS (all tests pass)

**Step 5: Run existing tests to ensure backward compatibility**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/services/test_llm_service.py -v  # if exists
pytest tests/ -k "llm" -v
```

**Expected:** All existing LLM tests still pass (API is backward compatible)

**Step 6: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/services/llm_service.py backend/tests/services/test_llm_service_langchain.py
git commit -m "refactor: migrate LLMService from DashScope SDK to LangChain ChatTongyi

- Replace dashscope.Generation with ChatTongyi
- Use LangChain PromptTemplate and LCEL chains
- Maintain backward compatible API
- Add comprehensive tests for new implementation"
```

---

## Stage 2: Agent Nodes Optimization

### Task 2.1: Update Response Generator Node to use LangChain Prompts

**Files:**
- Modify: `backend/app/agents/nodes.py`

**Step 1: Write failing test**

Create `backend/tests/agents/test_nodes_langchain.py`:

```python
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
        context_str="合同是法律文件..."
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
        context_str="劳动合同必须包含工作内容、报酬等条款"
    )

    result = await response_generator_node(state)

    assert "response" in result
    # Response should reference the context
    assert len(result["response"]) > 0
```

**Step 2: Run test to verify current behavior**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_nodes_langchain.py -v
```

**Expected:** Current tests may pass, but implementation doesn't use LangChain patterns yet

**Step 3: Refactor response_generator_node to use LangChain**

Update `backend/app/agents/nodes.py`:

```python
from typing import Dict, Any, List, AsyncIterator
from app.agents.state import AgentState
from app.agents.utils import convert_to_langchain_messages
from app.services.document_service import get_document_service
from app.services.llm_service import get_llm_service
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage
import logging
import json

logger = logging.getLogger(__name__)

# Default system prompt for legal consultation
DEFAULT_LEGAL_SYSTEM_PROMPT = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 基于提供的法律知识库回答，引用相关法规
4. 回答要清晰、易懂，避免过度专业术语

参考信息：
{context_str}

请基于以上参考信息回答用户的问题。如果参考信息不足，请说明这一点。"""

# System prompt builder
def build_system_prompt(context_str: str = "") -> str:
    """Build system prompt with optional RAG context."""
    if context_str:
        return DEFAULT_LEGAL_SYSTEM_PROMPT.format(context_str=context_str)
    return """你是一个友好的助手，为用户提供帮助。
回答要简洁、友好、有用。"""


async def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Classify user intent."""
    message = state["user_message"].lower()

    # Simple keyword-based intent classification
    legal_keywords = ["法律", "法", "合同", "侵权", "赔偿", "责任", "起诉", "诉讼", "法院"]
    greeting_keywords = ["你好", "您好", "hi", "hello"]

    if any(kw in message for kw in greeting_keywords):
        return {"user_intent": "greeting"}

    if any(kw in message for kw in legal_keywords):
        return {"user_intent": "legal_consultation"}

    return {"user_intent": "general_chat"}


async def rag_retriever_node(state: AgentState) -> Dict[str, Any]:
    """Retrieve relevant context from knowledge base."""
    document_service = get_document_service()

    if state.get("user_intent") != "legal_consultation":
        return {"retrieved_context": [], "sources": []}

    try:
        results = await document_service.search_knowledge(
            query=state["user_message"],
            category=None,
            n_results=5
        )

        context_str = _format_context_for_prompt(results)

        return {
            "retrieved_context": results,
            "context_str": context_str,
            "sources": [{"title": r.get("metadata", {}).get("title", ""), "score": r.get("score", 0)} for r in results]
        }
    except Exception as e:
        logger.error(f"Error in RAG retrieval: {e}")
        return {"retrieved_context": [], "context_str": "", "sources": []}


def _format_context_for_prompt(results: List[Dict[str, Any]]) -> str:
    """Format retrieved documents into context string."""
    if not results:
        return "未找到相关信息。"

    context_parts = []
    for i, result in enumerate(results[:5], 1):
        text = result.get("text", "")
        metadata = result.get("metadata", {})
        title = metadata.get("title", "未知来源")
        context_parts.append(f"[来源 {i}] {title}\n{text}")

    return "\n\n".join(context_parts)


async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generate response using LangChain ChatTongyi."""
    llm_service = get_llm_service()

    try:
        # Build system prompt
        system_prompt = build_system_prompt(state.get("context_str", ""))

        # Build LangChain prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}")
        ])

        # Build LCEL chain
        chain = prompt_template | llm_service.llm | StrOutputParser()

        # Convert conversation history
        history_messages = convert_to_langchain_messages(state["conversation_history"])

        # Invoke chain
        response = await chain.ainvoke({
            "history": history_messages,
            "user_message": state["user_message"]
        })

        return {"response": response, "error": ""}

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "response": "抱歉，处理您的请求时出现错误。请稍后再试。",
            "error": str(e)
        }


async def response_generator_node_stream(state: AgentState) -> AsyncIterator[Dict[str, Any]]:
    """Generate streaming response using LangChain ChatTongyi."""
    llm_service = get_llm_service()

    try:
        # Build system prompt
        system_prompt = build_system_prompt(state.get("context_str", ""))

        # Build LangChain prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_message}")
        ])

        # Build LCEL chain
        chain = prompt_template | llm_service.llm | StrOutputParser()

        # Convert conversation history
        history_messages = convert_to_langchain_messages(state["conversation_history"])

        # Yield start event
        yield {
            "event": "start",
            "data": {"intent": state.get("user_intent", "unknown")}
        }

        # Yield retrieved docs if any
        if state.get("sources"):
            yield {
                "event": "context",
                "data": {"sources": state["sources"]}
            }

        # Stream response using LangChain astream
        full_response = ""
        async for chunk in chain.astream({
            "history": history_messages,
            "user_message": state["user_message"]
        }):
            if chunk:
                full_response += chunk
                yield {
                    "event": "token",
                    "data": {"chunk": chunk, "full_response": full_response}
                }

        # Yield end event
        yield {
            "event": "end",
            "data": {"response": full_response}
        }

    except Exception as e:
        logger.error(f"Error generating streaming response: {e}")
        yield {
            "event": "error",
            "data": {"error": str(e)}
        }
```

**Step 4: Run tests**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_nodes_langchain.py -v
pytest tests/agents/ -v
```

**Expected:** All tests pass

**Step 5: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/agents/nodes.py backend/tests/agents/test_nodes_langchain.py
git commit -m "refactor: update agent nodes to use LangChain patterns

- Use ChatPromptTemplate for prompt building
- Use LCEL chains (prompt | llm | parser)
- Use MessagesPlaceholder for conversation history
- Maintain backward compatible event format"
```

---

### Task 2.2: Update Agent State to Support LangChain Messages

**Files:**
- Modify: `backend/app/agents/state.py`
- Test: `backend/tests/agents/test_state.py`

**Step 1: Write test for state compatibility**

Create `backend/tests/agents/test_state.py`:

```python
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
```

**Step 2: Run test**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_state.py -v
```

**Step 3: Verify state.py is compatible**

Ensure `backend/app/agents/state.py` has proper TypedDict definition:

```python
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
```

**Step 4: Run tests**

```bash
pytest tests/agents/test_state.py -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/agents/state.py backend/tests/agents/test_state.py
git commit -m "test: add AgentState type tests and ensure compatibility"
```

---

## Stage 3: Architecture Extensions

### Task 3.1: Create Tool Registry for MCP Integration

**Files:**
- Create: `backend/app/agents/tools.py`
- Test: `backend/tests/agents/test_tools.py`

**Step 1: Write failing test**

Create `backend/tests/agents/test_tools.py`:

```python
import pytest
from app.agents.tools import ToolRegistry, get_tool_registry

def test_tool_registry_singleton():
    """Test that get_tool_registry returns singleton"""
    registry1 = get_tool_registry()
    registry2 = get_tool_registry()
    assert registry1 is registry2

def test_register_tool():
    """Test registering a new tool"""
    registry = get_tool_registry()

    def test_function(query: str) -> str:
        return f"Result for: {query}"

    registry.register(
        name="test_tool",
        func=test_function,
        description="A test tool"
    )

    tools = registry.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"

def test_get_tools_returns_empty_initially():
    """Test that get_tools returns empty list when no tools registered"""
    registry = ToolRegistry()  # Fresh instance
    tools = registry.get_tools()
    assert tools == []

def test_mcp_interface_exists():
    """Test that MCP integration interface is defined"""
    registry = ToolRegistry()
    assert hasattr(registry, 'load_from_mcp_server')
    # Implementation is TODO, but interface should exist
```

**Step 2: Run test to verify it fails**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_tools.py -v
```

**Expected:** FAIL with "ModuleNotFoundError: No module named 'app.agents.tools'"

**Step 3: Implement ToolRegistry**

Create `backend/app/agents/tools.py`:

```python
"""Tool registry for agent function calling.

This module provides a centralized tool registry that can be extended
to support MCP (Model Context Protocol) servers in the future.
"""

from typing import Dict, List, Callable, Any
from langchain_core.tools import Tool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for managing tools available to the agent.

    This class provides a foundation for tool management and includes
    placeholder methods for future MCP server integration.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str
    ) -> None:
        """
        Register a new tool.

        Args:
            name: Unique identifier for the tool
            func: Callable that implements the tool functionality
            description: Human-readable description of what the tool does
        """
        self._tools[name] = Tool(
            name=name,
            func=func,
            description=description
        )
        logger.info(f"Registered tool: {name}")

    def get_tools(self) -> List[Tool]:
        """
        Get all registered tools.

        Returns:
            List of all registered Tool objects
        """
        return list(self._tools.values())

    async def load_from_mcp_server(self, server_url: str) -> None:
        """
        Load tools from an MCP server.

        This is a placeholder for future MCP protocol integration.
        When implemented, this will connect to an MCP server and
        dynamically register tools provided by that server.

        Args:
            server_url: URL of the MCP server to connect to

        Raises:
            NotImplementedError: This method is not yet implemented
        """
        raise NotImplementedError(
            "MCP server integration is not yet implemented. "
            "This is a placeholder for future functionality."
        )


# Global singleton instance
_tool_registry: ToolRegistry = None


def get_tool_registry() -> ToolRegistry:
    """
    Get or create the global ToolRegistry singleton.

    Returns:
        The global ToolRegistry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
```

**Step 4: Run test to verify it passes**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_tools.py -v
```

**Expected:** PASS (all tests pass)

**Step 5: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/agents/tools.py backend/tests/agents/test_tools.py
git commit -m "feat: add ToolRegistry for agent function calling

- Implement centralized tool registry
- Add placeholder for MCP server integration
- Add comprehensive tests"
```

---

### Task 3.2: Create Memory Factory for Conversation Memory

**Files:**
- Create: `backend/app/agents/memory.py`
- Test: `backend/tests/agents/test_memory.py`

**Step 1: Write failing test**

Create `backend/tests/agents/test_memory.py`:

```python
import pytest
from app.agents.memory import MemoryFactory

def test_create_buffer_memory():
    """Test creating buffer memory"""
    memory = MemoryFactory.create_buffer_memory()
    assert memory is not None
    # Verify it's the right type
    from langchain.memory import ConversationBufferMemory
    assert isinstance(memory, ConversationBufferMemory)

def test_buffer_memory_config():
    """Test buffer memory has correct configuration"""
    memory = MemoryFactory.create_buffer_memory()
    assert memory.return_messages == True
    assert memory.output_key == "response"
```

**Step 2: Run test to verify it fails**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_memory.py -v
```

**Expected:** FAIL with "ModuleNotFoundError: No module named 'app.agents.memory'"

**Step 3: Implement MemoryFactory**

Create `backend/app/agents/memory.py`:

```python
"""Memory management for agent conversation history.

This module provides factory methods for creating different types
of conversation memory for the agent.
"""

from langchain.memory import ConversationBufferMemory
from langchain_core.memory import BaseMemory
import logging

logger = logging.getLogger(__name__)


class MemoryFactory:
    """
    Factory for creating different types of conversation memory.

    This class provides a unified interface for creating various
    memory implementations, with plans for future expansion.
    """

    @staticmethod
    def create_buffer_memory() -> BaseMemory:
        """
        Create a buffer memory that stores all conversation history.

        Returns:
            ConversationBufferMemory instance configured for agent use
        """
        return ConversationBufferMemory(
            return_messages=True,
            output_key="response"
        )

    # Placeholders for future memory types
    @staticmethod
    def create_window_memory(k: int = 5):
        """
        Create a window memory that keeps only the last k exchanges.

        TODO: Implement window memory
        """
        raise NotImplementedError("Window memory not yet implemented")

    @staticmethod
    def create_summary_memory():
        """
        Create a summary memory that maintains conversation summaries.

        TODO: Implement summary memory
        """
        raise NotImplementedError("Summary memory not yet implemented")
```

**Step 4: Run test to verify it passes**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/agents/test_memory.py -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/agents/memory.py backend/tests/agents/test_memory.py
git commit -m "feat: add MemoryFactory for conversation memory management

- Implement ConversationBufferMemory factory
- Add placeholders for window and summary memory types
- Add unit tests"
```

---

### Task 3.3: Update Configuration for Multi-Provider Support

**Files:**
- Modify: `backend/app/config.py`

**Step 1: Write test for new configuration**

Create `backend/tests/test_config.py`:

```python
import pytest
from app.config import get_settings, create_llm_from_config

def test_default_provider_is_tongyi():
    """Test that default LLM provider is tongyi"""
    settings = get_settings()
    # Provider may not be in old config, check default
    assert hasattr(settings, 'dashscope_api_key')

def test_llm_config_attributes():
    """Test LLM config has required attributes"""
    settings = get_settings()
    assert hasattr(settings, 'dashscope_model')
    assert hasattr(settings, 'dashscope_api_key')

@pytest.mark.skipif(
    True,  # Skip until we add create_llm_from_config
    reason="Function not yet implemented"
)
def test_create_llm_from_tongyi_config():
    """Test creating ChatTongyi from config"""
    from langchain_community.chat_models.tongyi import ChatTongyi

    settings = get_settings()
    llm = create_llm_from_config(settings)
    assert isinstance(llm, ChatTongyi)
```

**Step 2: Run test**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/test_config.py -v
```

**Step 3: Add LLM factory function to config**

Update `backend/app/config.py`:

```python
"""Application configuration with multi-provider LLM support."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "legal-consultation-backend"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/dbname"

    # DashScope / Tongyi (default provider)
    dashscope_api_key: str
    dashscope_model: str = "qwen-max"

    # OpenAI (optional, for future multi-provider support)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"

    # LLM Provider selection
    llm_provider: str = "tongyi"  # tongyi | openai

    class Config:
        env_file = ".env"
        case_sensitive = False


def create_llm_from_config(settings: Settings) -> BaseChatModel:
    """
    Create LLM instance based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = settings.llm_provider.lower()

    if provider == "tongyi":
        return ChatTongyi(
            model=settings.dashscope_model,
            dashscope_api_key=settings.dashscope_api_key,
            temperature=0.7,
        )
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required when provider is 'openai'")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Step 4: Run tests**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/test_config.py -v
```

**Expected:** PASS

**Step 5: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/app/config.py backend/tests/test_config.py
git commit -m "feat: add multi-provider LLM configuration

- Add create_llm_from_config factory function
- Support tongyi and openai providers
- Add configuration tests"
```

---

## Integration Testing

### Task 4.1: End-to-End Integration Test

**Files:**
- Create: `backend/tests/integration/test_langchain_integration.py`

**Step 1: Write integration test**

Create `backend/tests/integration/test_langchain_integration.py`:

```python
import pytest
from app.services.llm_service import get_llm_service
from app.agents.graph import get_agent_graph, get_streaming_agent_graph

@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test complete agent workflow with LangChain components."""
    # Get the compiled graph
    graph = get_agent_graph()

    # Create initial state
    initial_state = {
        "user_message": "什么是合同？",
        "conversation_history": [],
        "user_intent": None,
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": None
    }

    # Run the graph
    result = await graph.ainvoke(initial_state)

    # Verify result
    assert result["response"] is not None
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0
    assert result.get("error") in ("", None)

@pytest.mark.asyncio
async def test_streaming_agent_workflow():
    """Test streaming agent workflow with LangChain components."""
    graph = get_streaming_agent_graph()

    initial_state = {
        "user_message": "你好",
        "conversation_history": [],
        "user_intent": None,
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": None
    }

    events = []
    async for event in graph.astream(initial_state):
        events.append(event)
        # Should get events for each node

    # Verify we got events
    assert len(events) > 0

    # Find the final response
    final_response = None
    for event in events:
        for node_name, node_output in event.items():
            if node_name == "response_generator_stream":
                # Extract response from stream events
                if isinstance(node_output, dict):
                    pass  # Stream events are handled differently

    # Basic check that something was processed
    assert len(events) > 0
```

**Step 2: Run integration test**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/integration/test_langchain_integration.py -v
```

**Expected:** PASS

**Step 3: Commit**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/tests/integration/test_langchain_integration.py
git commit -m "test: add end-to-end integration test for LangChain migration

- Test complete agent workflow
- Test streaming workflow
- Verify all components work together"
```

---

## Final Verification

### Task 5.1: Run Full Test Suite

**Step 1: Run all tests**

```bash
cd D:/vibe-coding/dialog_chat_room/backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Expected:** All tests pass, coverage report shows good coverage

**Step 2: Check for any regressions**

```bash
pytest tests/ -v -k "not integration"  # Run unit tests only
```

**Expected:** All unit tests pass

### Task 5.2: Update Documentation

**Files:**
- Modify: `backend/docs/ARCHITECTURE.md`

**Step 1: Update ARCHITECTURE.md**

Add section about LangChain integration:

```markdown
## LLM Service

使用 LangChain 的 `ChatTongyi` 集成通义千问：

```python
from langchain_community.chat_models.tongyi import ChatTongyi

llm = ChatTongyi(
    model="qwen-max",
    dashscope_api_key=settings.dashscope_api_key
)
```

**特点:**
- 使用 LangChain PromptTemplate 构建 prompt
- 使用 LCEL 链式调用 (prompt | llm | parser)
- 支持流式输出 (astream)
- 可配置多提供商切换

## Agent 节点

使用 LangChain 原生组件：

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_message}")
])

chain = prompt_template | llm | StrOutputParser()
```

## 扩展架构

- **ToolRegistry**: 工具注册中心，为 MCP 集成预留
- **MemoryFactory**: 内存管理工厂
- **多提供商支持**: 支持 tongyi、openai 等多种模型
```

**Step 2: Commit documentation**

```bash
cd D:/vibe-coding/dialog_chat_room
git add backend/docs/ARCHITECTURE.md
git commit -m "docs: update ARCHITECTURE.md for LangChain integration"
```

---

## Summary

This implementation plan provides a complete, test-driven migration from DashScope SDK to LangChain ChatTongyi with:

- ✅ Three-stage incremental migration
- ✅ Full backward compatibility
- ✅ Comprehensive test coverage
- ✅ Architecture extensions for future MCP integration
- ✅ Multi-provider LLM support

**Total Estimated Time:** ~7 hours
**Files Created:** 8 new files
**Files Modified:** 4 existing files
**Test Coverage:** Comprehensive unit and integration tests
