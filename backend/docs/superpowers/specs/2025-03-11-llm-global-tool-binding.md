# LLM 全局工具绑定设计

**Date:** 2025-03-11
**Status:** Design Approved

## Goal

让 LLM 在所有对话节点中都知道系统的工具能力（如案例搜索），当用户直接问"你能搜索案例吗？"时，LLM 能够回答并主动调用工具。

## Problem Statement

当前设计中，工具只在特定节点中绑定（如 `case_search_node` 中的 `search_cases`），导致：

1. 用户在普通对话中问"你能搜索案例吗？"时，LLM 不知道有这个功能
2. 必须通过按钮触发 `search_cases:` 命令才能使用
3. 用户体验不自然，无法直接与 LLM 对话来使用工具

## Solution

在 `response_generator_node` 中也绑定工具，让 LLM 在所有对话中都知道系统能力。

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户对话流程（改进后）                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户："你能搜索案例吗？"                                        │
│     ↓                                                           │
│  response_generator_node                                        │
│     ↓                                                           │
│  ┌─────────────────────────────────────────────┐                │
│  │ LLM (已绑定 search_cases 工具)              │                │
│  │                                             │                │
│  │ 系统提示词:                                  │                │
│  │ "你有以下能力：                               │                │
│  │  - search_cases: 搜索法律案例"               │                │
│  │                                             │                │
│  │ 工具描述（bind_tools 提供）：                │                │
│  │ search_cases(query, limit) → 搜索案例       │                │
│  └─────────────────────────────────────────────┘                │
│     ↓                                                           │
│  LLM 回复："可以的！我可以帮您搜索相关法律案例。请告诉我您想      │
│           搜索什么类型的案例？"                                  │
│                                                                 │
│  用户："交通事故赔偿"                                            │
│     ↓                                                           │
│  LLM 自动调用 search_cases 工具                                  │
│     ↓                                                           │
│  展示搜索结果                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. 工具能力配置

**File:** `backend/app/agents/tools/capabilities.py` (new file)

```python
"""工具能力配置 - 定义系统中所有可用的工具及其元数据"""
from typing import Dict, List, Optional
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
        llm_bindable=True  # LLM 可以直接调用
    ),
    "memory_extraction": ToolConfig(
        enabled=True,
        description="提取和存储用户长期记忆和偏好",
        requires_api_key=False,
        llm_bindable=False  # 仅内部使用，LLM 不直接调用
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
        if config and config.enabled:
            tools_desc.append(f"- {tool_name}: {config.description}")

    if not tools_desc:
        return ""

    return "你可以使用以下功能：\n" + "\n".join(tools_desc)
```

### 2. 系统提示词增强

**File:** `backend/app/agents/nodes.py` (modify existing)

```python
def build_system_prompt_with_tools() -> str:
    """构建包含工具能力的系统提示词"""
    from app.agents.tools.capabilities import get_tools_description

    base_prompt = build_system_prompt()
    tools_desc = get_tools_description()

    if not tools_desc:
        return base_prompt

    return f"{base_prompt}\n\n{tools_desc}\n请在用户需要时主动使用这些功能。"
```

### 3. response_generator_node 修改

**File:** `backend/app/agents/nodes.py` (modify existing)

**Changes:**
1. 导入工具相关模块
2. 构建包含工具的系统提示词
3. 获取启用的工具并绑定到 LLM

```python
async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """Generate response using LangChain ChatTongyi with memory and tools."""
    from app.agents.tools import get_tool_registry
    from app.agents.tools.capabilities import get_llm_bound_tools

    llm_service = get_llm_service()
    tool_registry = get_tool_registry()

    # 构建包含工具的系统提示词
    system_prompt = build_system_prompt_with_tools()

    # ... 现有的记忆增强逻辑保持不变 ...

    # 获取启用的工具
    tools = []
    for tool_name in get_llm_bound_tools():
        tool = tool_registry.get_tool(tool_name)
        if tool:
            tools.append(tool)

    # 构建链
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_message}")
    ])

    # 绑定工具到 LLM（如果有工具）
    if tools:
        try:
            llm_with_tools = llm_service.llm.bind_tools(tools)
            chain = prompt_template | llm_with_tools | StrOutputParser()
        except AttributeError:
            # LLM 不支持 bind_tools()，降级为普通对话
            logger.warning("LLM does not support bind_tools(), falling back to plain LLM")
            chain = prompt_template | llm_service.llm | StrOutputParser()
    else:
        chain = prompt_template | llm_service.llm | StrOutputParser()

    # ... 现有的执行逻辑保持不变 ...
```

### 4. 工具可用性检查

**File:** `backend/app/agents/tools/capabilities.py` (add to existing)

```python
def check_tool_availability(tool_name: str) -> tuple[bool, str]:
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

### 5. response_generator_node_stream 同步修改

**File:** `backend/app/agents/nodes.py` (modify existing)

同样需要修改 `response_generator_node_stream` 函数以支持工具绑定：

```python
async def response_generator_node_stream(state: AgentState) -> AsyncIterator[Dict[str, Any]]:
    """Generate streaming response using LangChain ChatTongyi with memory and tools."""
    from app.agents.tools import get_tool_registry
    from app.agents.tools.capabilities import get_llm_bound_tools

    llm_service = get_llm_service()
    tool_registry = get_tool_registry()

    # 构建包含工具的系统提示词
    system_prompt = build_system_prompt_with_tools()

    # ... 现有的记忆增强逻辑保持不变 ...

    # 获取启用的工具
    tools = []
    for tool_name in get_llm_bound_tools():
        tool = tool_registry.get_tool(tool_name)
        if tool:
            tools.append(tool)

    # 构建链
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_message}")
    ])

    # 绑定工具到 LLM（如果有工具）
    if tools:
        try:
            llm_with_tools = llm_service.llm.bind_tools(tools)
            chain = prompt_template | llm_with_tools | StrOutputParser()
        except AttributeError:
            logger.warning("LLM does not support bind_tools(), falling back to plain LLM")
            chain = prompt_template | llm_service.llm | StrOutputParser()
    else:
        chain = prompt_template | llm_service.llm | StrOutputParser()

    # ... 现有的流式输出逻辑保持不变 ...
```

## Data Flow

```
用户消息进入
    ↓
intent_router → 根据意图路由
    ↓
┌─────────────┬──────────────┬─────────────────┐
│             │              │                 │
│ legal_       │ case_        │ general/        │
│ consultation │ search       │ greeting        │
│             │              │                 │
│ ↓           │ ↓            │ ↓               │
│ rag_         │ case_        │ response_       │
│ retriever    │ search_node  │ generator_node  │
│             │              │                 │
│             │              │ ✅ 现在也绑定工具 │
│ ↓           │ ↓            │ ↓               │
└─────────────┴──────────────┴─────────────────┘
    ↓              ↓               ↓
response_generator (最终都到这里)
```

## Error Handling

| 场景 | 处理方式 |
|------|----------|
| 工具未启用 | LLM 不会在系统提示词中看到该工具 |
| API 密钥缺失 | 工具执行时返回友好错误 |
| 工具执行失败 | LLM 收到错误信息，告知用户重试 |
| LLM 不调用工具 | 正常对话，降级为纯文本回复 |

## Testing

### Unit Tests

**File:** `tests/agents/tools/test_capabilities.py`

```python
def test_get_enabled_tools():
    tools = get_enabled_tools()
    assert "search_cases" in tools

def test_get_llm_bound_tools():
    tools = get_llm_bound_tools()
    assert "search_cases" in tools

def test_get_tools_description():
    desc = get_tools_description()
    assert "search_cases" in desc
    assert "搜索" in desc

def test_check_tool_availability():
    available, msg = check_tool_availability("search_cases")
    # 取决于 FIRECRAWL_API_KEY 是否配置
```

### Integration Tests

**File:** `tests/agents/test_response_generator_with_tools.py`

```python
async def test_response_generator_has_tools_bound():
    """验证 response_generator_node 正确绑定工具"""
    state = create_initial_state(
        user_message="你能搜索案例吗？",
        conversation_history=[],
        user_id=None,
        session_id="test",
        streaming=False
    )
    result = await response_generator_node(state)
    # 验证 LLM 知道有 search_cases 功能
    assert "可以" in result["response"] or "搜索" in result["response"]
```

### E2E Tests

**File:** `tests/e2e/test_tool_conversation.py`

```python
class TestToolConversation:
    """端到端测试：用户直接与 LLM 对话使用工具"""

    @pytest.mark.asyncio
    async def test_user_asks_about_search_capability(self, test_client):
        """
        完整对话流程：
        1. 用户问"你能搜索案例吗？"
        2. LLM 回答"可以"并询问搜索类型
        3. 用户提供搜索关键词"交通事故赔偿"
        4. LLM 自动调用 search_cases 工具
        5. 验证搜索结果正确返回
        """
        # 第一轮：用户询问能力
        response1 = await send_message("你能搜索案例吗？")
        assert "可以" in response1 or "搜索" in response1

        # 第二轮：用户提供搜索关键词
        response2 = await send_message("交通事故赔偿")
        # 验证包含了案例相关信息
        assert "案例" in response2 or "裁判" in response2 or "法院" in response2

    @pytest.mark.asyncio
    async def test_tool_fails_gracefully_when_api_key_missing(self):
        """测试：API 密钥缺失时优雅降级"""
        # 临时移除 API 密钥
        original_key = os.environ.get("FIRECRAWL_API_KEY")
        os.environ["FIRECRAWL_API_KEY"] = ""

        try:
            response = await send_message("帮我搜索劳动合同纠纷的案例")
            # 应该返回友好的错误信息，而不是崩溃
            assert "未配置" in response or "暂不可用" in response
        finally:
            if original_key:
                os.environ["FIRECRAWL_API_KEY"] = original_key
```

## Backward Compatibility

✅ **完全向后兼容**
- 现有的按钮触发方式仍然有效
- 现有的 `search_cases:` 命令仍然有效
- 只是增加了 LLM 直接调用的能力

## Future Enhancements

1. **更多工具绑定** - 将其他工具（如文档分析）也添加到 LLM 绑定
2. **工具权限控制** - 根据用户角色决定可用工具
3. **工具使用统计** - 记录工具调用频率
4. **智能降级** - API 密钥缺失时自动禁用工具

## Dependencies

- LangChain `bind_tools()` 支持
- ChatTongyi 工具调用支持
- 现有 ToolRegistry 基础设施
