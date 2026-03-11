# LLM 全局工具绑定实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 LLM 在所有对话中都知道系统的工具能力，用户可以直接问"你能搜索案例吗？"来使用功能。

**Architecture:** 在 `response_generator_node` 中绑定工具到 LLM，通过 `capabilities.py` 配置哪些工具可以被 LLM 直接调用。

**Tech Stack:** Python, LangChain, ChatTongyi, Pydantic

---

## File Structure

```
backend/app/agents/tools/
├── __init__.py           # ToolRegistry（注册）
├── capabilities.py       # AVAILABLE_TOOLS（配置）← 新增
├── case_search.py        # search_cases 工具实现

backend/app/agents/
├── nodes.py              # response_generator_node 修改

tests/agents/tools/
└── test_capabilities.py  # 单元测试 ← 新增
```

---

## Chunk 1: 创建工具能力配置模块

### Task 1: 创建 capabilities.py 基础结构

**Files:**
- Create: `backend/app/agents/tools/capabilities.py`
- Test: `tests/agents/tools/test_capabilities.py`

- [ ] **Step 1: Write the failing test**

创建 `tests/agents/tools/test_capabilities.py`:

```python
"""Tests for tool capabilities configuration."""
import pytest
from app.agents.tools.capabilities import (
    ToolConfig,
    AVAILABLE_TOOLS,
    get_enabled_tools,
    get_llm_bound_tools,
    get_tools_description
)

class TestToolConfig:
    def test_tool_config_creation(self):
        """Test creating a ToolConfig"""
        config = ToolConfig(
            enabled=True,
            description="测试工具",
            requires_api_key=False,
            llm_bindable=True
        )
        assert config.enabled is True
        assert config.description == "测试工具"
        assert config.llm_bindable is True

class TestAvailableTools:
    def test_available_tools_structure(self):
        """Test AVAILABLE_TOOLS has correct structure"""
        assert "search_cases" in AVAILABLE_TOOLS
        assert "memory_extraction" in AVAILABLE_TOOLS

        config = AVAILABLE_TOOLS["search_cases"]
        assert isinstance(config, ToolConfig)
        assert config.enabled is True
        assert config.llm_bindable is True

        mem_config = AVAILABLE_TOOLS["memory_extraction"]
        assert mem_config.llm_bindable is False

class TestGetEnabledTools:
    def test_returns_enabled_tools_only(self):
        """Test that only enabled tools are returned"""
        tools = get_enabled_tools()
        assert "search_cases" in tools
        assert "memory_extraction" in tools

class TestGetLLMBoundTools:
    def test_returns_llm_bindable_tools_only(self):
        """Test that only llm_bindable tools are returned"""
        tools = get_llm_bound_tools()
        assert "search_cases" in tools
        assert "memory_extraction" not in tools  # Not llm_bindable

class TestGetToolsDescription:
    def test_returns_description_string(self):
        """Test that tools description is generated"""
        desc = get_tools_description()
        assert "search_cases" in desc
        assert "搜索" in desc or "案例" in desc
```

- [ ] **Step 2: Run test to verify it fails**

运行: `cd backend && pytest tests/agents/tools/test_capabilities.py -v`
预期: FAIL - ModuleNotFoundError: No module named 'app.agents.tools.capabilities'

- [ ] **Step 3: Write minimal implementation**

创建 `backend/app/agents/tools/capabilities.py`:

```python
"""工具能力配置 - 定义系统中所有可用的工具及其元数据"""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

class ToolConfig(BaseModel):
    """单个工具的配置"""
    enabled: bool = True
    description: str = ""
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None
    llm_bindable: bool = True  # LLM 是否可以直接调用此工具

# 所有可用工具的配置
AVAILABLE_TOOLS: Dict[str, ToolConfig] = {
    "search_cases": ToolConfig(
        enabled=True,
        description="搜索相关法律案例和裁判文书",
        requires_api_key=True,
        api_key_env_var="FIRECRAWL_API_KEY",
        llm_bindable=True
    ),
    "memory_extraction": ToolConfig(
        enabled=True,
        description="提取和存储用户长期记忆和偏好",
        requires_api_key=False,
        llm_bindable=False
    ),
}

def get_enabled_tools() -> List[str]:
    """获取所有启用的工具名称"""
    return [name for name, config in AVAILABLE_TOOLS.items()
            if config.enabled]

def get_llm_bound_tools() -> List[str]:
    """获取应该绑定到 LLM 的工具（用户可直接调用的）"""
    return [name for name, config in AVAILABLE_TOOLS.items()
            if config.enabled and config.llm_bindable]

def get_tools_description() -> str:
    """获取工具描述，用于系统提示词"""
    tools_desc = []
    for tool_name in get_llm_bound_tools():
        config = AVAILABLE_TOOLS.get(tool_name)
        if config:
            tools_desc.append(f"- {tool_name}: {config.description}")

    if not tools_desc:
        return ""

    return "你可以使用以下功能：\n" + "\n".join(tools_desc)

def check_tool_availability(tool_name: str) -> Tuple[bool, str]:
    """检查工具是否可用

    Returns:
        (available, error_message)
    """
    from app.config import get_settings

    config = AVAILABLE_TOOLS.get(tool_name)
    if not config:
        return False, "工具不存在"

    if not config.enabled:
        return False, "工具未启用"

    if config.requires_api_key:
        settings = get_settings()
        api_key = getattr(settings, config.api_key_env_var or "", "")
        if not api_key:
            return False, f"需要配置 {config.api_key_env_var}"

    return True, ""
```

- [ ] **Step 4: Run test to verify it passes**

运行: `cd backend && pytest tests/agents/tools/test_capabilities.py -v`
预期: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/tools/capabilities.py tests/agents/tools/test_capabilities.py
git commit -m "feat: add tool capabilities configuration

- Create ToolConfig with enabled, description, llm_bindable fields
- Define AVAILABLE_TOOLS for search_cases and memory_extraction
- Add helper functions: get_enabled_tools, get_llm_bound_tools, etc.
- Add unit tests for capabilities module

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: 修改 response_generator_node

### Task 2: 添加系统提示词增强函数

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: Add build_system_prompt_with_tools function**

在 `backend/app/agents/nodes.py` 中 `build_system_prompt` 函数之后添加：

```python
def build_system_prompt_with_tools(context_str: str = "") -> str:
    """Build system prompt with optional RAG context and tool capabilities."""
    from app.agents.tools.capabilities import get_tools_description

    # Build base prompt
    base_prompt = build_system_prompt(context_str)

    # Add tools description
    tools_desc = get_tools_description()

    if not tools_desc:
        return base_prompt

    return f"{base_prompt}\n\n{tools_desc}\n请在用户需要时主动使用这些功能。"
```

- [ ] **Step 2: Run existing tests to verify no breakage**

运行: `cd backend && pytest tests/agents/test_nodes_langchain.py -v`
预期: PASS - 现有测试仍然通过

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/nodes.py
git commit -m "feat: add build_system_prompt_with_tools helper

- Import get_tools_description from capabilities
- Append tool capabilities to base system prompt
- Maintain backward compatibility (returns base prompt if no tools)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Task 3: 修改 response_generator_node 绑定工具

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: Modify response_generator_node to use tools**

找到 `response_generator_node` 函数，按以下方式修改：

**在函数开头添加导入：**
```python
async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generate response using LangChain ChatTongyi with memory and tools."""
    from app.agents.tools import get_tool_registry
    from app.agents.tools.capabilities import get_llm_bound_tools
    # ... rest of function
```

**替换 system_prompt 构建：**
找到:
```python
system_prompt = build_system_prompt(state.get("context_str", ""))
```
替换为:
```python
system_prompt = build_system_prompt_with_tools(state.get("context_str", ""))
```

**在 memory enhancement 之后、chain 构建之前添加工具绑定：**

在 `# Build LangChain prompt template` 之前添加：
```python
# Get enabled tools for LLM binding
tools = []
for tool_name in get_llm_bound_tools():
    tool = tool_registry.get_tool(tool_name)
    if tool:
        tools.append(tool)
```

**替换 chain 构建：**

找到:
```python
chain = prompt_template | llm_service.llm | StrOutputParser()
```

替换为:
```python
# Bind tools to LLM (if any tools available)
if tools:
    try:
        llm_with_tools = llm_service.llm.bind_tools(tools)
        chain = prompt_template | llm_with_tools | StrOutputParser()
    except AttributeError:
        # LLM doesn't support bind_tools()
        logger.warning("LLM does not support bind_tools(), falling back to plain LLM")
        chain = prompt_template | llm_service.llm | StrOutputParser()
else:
    chain = prompt_template | llm_service.llm | StrOutputParser()
```

- [ ] **Step 2: Run tests to verify**

运行: `cd backend && pytest tests/agents/test_nodes_langchain.py tests/agents/test_graph_execution.py -v`
预期: PASS - 所有测试通过

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/nodes.py
git commit -m "feat: bind tools to LLM in response_generator_node

- Import tool_registry and capabilities modules
- Use build_system_prompt_with_tools to include tool descriptions
- Get llm_bound_tools and bind them to LLM with bind_tools()
- Add graceful fallback when bind_tools not supported
- Maintain backward compatibility

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Task 4: 同步修改 response_generator_node_stream

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: Apply same changes to streaming version**

找到 `response_generator_node_stream` 函数，应用与 Task 3 相同的修改：

1. 添加导入（在函数开头或文件顶部）
2. 替换 `build_system_prompt` 为 `build_system_prompt_with_tools`
3. 添加工具获取逻辑
4. 修改 chain 构建，添加 bind_tools() 和错误处理

参考 Task 3 中的代码修改。

- [ ] **Step 2: Run streaming tests**

运行: `cd backend && pytest tests/agents/test_graph_execution.py::test_graph_streaming_mode -v`
预期: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/nodes.py
git commit -m "feat: bind tools to LLM in response_generator_node_stream

- Apply same tool binding logic to streaming node
- Use build_system_prompt_with_tools for system prompt
- Add bind_tools() support with graceful fallback
- Ensure streaming works with tool-enabled LLM

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: 集成测试

### Task 5: 添加集成测试

**Files:**
- Create: `tests/agents/test_response_generator_with_tools.py`

- [ ] **Step 1: Write integration test**

创建 `tests/agents/test_response_generator_with_tools.py`:

```python
"""Tests for response_generator with tool binding."""
import pytest
from app.agents.nodes import response_generator_node
from app.agents.state import AgentState

class TestResponseGeneratorWithTools:
    @pytest.mark.asyncio
    async def test_llm_has_tools_in_system_prompt(self):
        """Test that system prompt includes tool descriptions"""
        from app.agents.tools.capabilities import get_tools_description

        tools_desc = get_tools_description()
        assert "search_cases" in tools_desc

    @pytest.mark.asyncio
    async def test_response_generator_with_tool_calling(self):
        """Test that response_generator can handle tool binding"""
        state: AgentState = {
            "user_message": "你能搜索案例吗？",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test-session",
            "streaming": False
        }

        result = await response_generator_node(state)

        # Should have a response
        assert "response" in result
        assert isinstance(result["response"], str)
        # Should mention capability or ask what to search
        assert "可以" in result["response"] or "搜索" in result["response"] or "案例" in result["response"]

    @pytest.mark.asyncio
    async def test_response_generator_without_tool_calling(self):
        """Test that response_generator works for normal conversation"""
        state: AgentState = {
            "user_message": "你好",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test-session",
            "streaming": False
        }

        result = await response_generator_node(state)

        assert "response" in result
        assert result["error"] == ""
```

- [ ] **Step 2: Run test to verify**

运行: `cd backend && pytest tests/agents/test_response_generator_with_tools.py -v`
预期: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/agents/test_response_generator_with_tools.py
git commit -m "test: add integration tests for tool binding

- Test system prompt includes tool descriptions
- Test response_generator handles tool calling
- Test normal conversation still works
- Verify LLM responds to capability questions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: E2E 测试

### Task 6: 添加端到端测试

**Files:**
- Create: `tests/e2e/test_tool_conversation.py`

- [ ] **Step 1: Write E2E test**

创建 `tests/e2e/test_tool_conversation.py`:

```python
"""End-to-end tests for tool conversation flow."""
import pytest
import os

class TestToolConversation:
    """端到端测试：用户直接与 LLM 对话使用工具"""

    @pytest.mark.asyncio
    async def test_user_asks_about_search_capability(self, get_graph_with_tools):
        """
        完整对话流程：
        1. 用户问"你能搜索案例吗？"
        2. LLM 回答"可以"并询问搜索类型
        3. 用户提供搜索关键词"交通事故赔偿"
        4. LLM 自动调用 search_cases 工具
        """
        graph = get_graph_with_tools()

        # 第一轮：用户询问能力
        state1 = {
            "user_message": "你能搜索案例吗？",
            "conversation_history": [],
            "user_id": None,
            "session_id": "test-e2e",
            "streaming": False
        }
        result1 = await graph.ainvoke(state1)
        assert "response" in result1
        assert "可以" in result1["response"] or "搜索" in result1["response"]

        # 第二轮：用户提供搜索关键词
        state2 = {
            "user_message": "交通事故赔偿",
            "conversation_history": [
                {"role": "user", "content": "你能搜索案例吗？"},
                {"role": "assistant", "content": result1["response"]}
            ],
            "user_id": None,
            "session_id": "test-e2e",
            "streaming": False
        }
        result2 = await graph.ainvoke(state2)
        assert "response" in result2
        # Should contain search results or case-related info
        assert "案例" in result2["response"] or "裁判" in result2["response"] or "法院" in result2["response"]

    @pytest.mark.asyncio
    async def test_tool_fails_gracefully_when_api_key_missing(self, get_graph_with_tools):
        """测试：API 密钥缺失时优雅降级"""
        # 临时移除 API 密钥
        original_key = os.environ.get("FIRECRAWL_API_KEY")
        os.environ["FIRECRAWL_API_KEY"] = ""

        try:
            # 需要重新加载配置
            from importlib import reload
            import app.services.firecrawl_service
            reload(app.services.firecrawl_service)

            graph = get_graph_with_tools()
            state = {
                "user_message": "帮我搜索劳动合同纠纷的案例",
                "conversation_history": [],
                "user_id": None,
                "session_id": "test-missing-key",
                "streaming": False
            }
            result = await graph.ainvoke(state)

            # 应该返回友好的错误信息或说明需要配置
            assert "response" in result
            assert "未配置" in result["response"] or "暂不可用" in result["response"] or "需要" in result["response"]
        finally:
            if original_key:
                os.environ["FIRECRAWL_API_KEY"] = original_key


@pytest.fixture
async def get_graph_with_tools():
    """Fixture to get graph with tools enabled"""
    from app.agents.graph import get_unified_agent_graph
    return get_unified_agent_graph()
```

- [ ] **Step 2: Run E2E test**

运行: `cd backend && pytest tests/e2e/test_tool_conversation.py -v`
预期: PASS 或 SKIP（如果没有 API 密钥）

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_tool_conversation.py
git commit -m "test: add E2E tests for tool conversation flow

- Test user asking about search capability
- Test LLM auto-calling search_cases tool
- Test graceful degradation when API key missing
- Add get_graph_with_tools fixture

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 实现完成检查清单

完成所有任务后，验证以下内容：

- [ ] `backend/app/agents/tools/capabilities.py` 已创建
- [ ] `backend/app/agents/nodes.py` 已修改（response_generator_node 和 response_generator_node_stream）
- [ ] 所有单元测试通过: `pytest tests/agents/tools/test_capabilities.py -v`
- [ ] 所有节点测试通过: `pytest tests/agents/test_nodes_langchain.py -v`
- [ ] 所有图执行测试通过: `pytest tests/agents/test_graph_execution.py -v`
- [ ] 集成测试通过: `pytest tests/agents/test_response_generator_with_tools.py -v`
- [ ] E2E 测试通过: `pytest tests/e2e/test_tool_conversation.py -v`
- [ ] 手动测试：启动后端，问"你能搜索案例吗？"，然后提供关键词

---

## 环境变量配置

确保 `.env` 文件中有：

```bash
FIRECRAWL_API_KEY=fc-your_api_key_here
```

---

## 总计

**Tasks:** 6 个任务
**Estimated Steps:** ~30 步
**Estimated Time:** 2-3 小时
