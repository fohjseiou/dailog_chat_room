# LLM 服务迁移到 LangChain ChatTongyi 设计文档

**日期**: 2026-03-10
**状态**: 设计中
**方案**: 方案 A - 渐进式 LangChain 化

---

## 需求概述

将后端 LLM 服务从 DashScope 原生 SDK 迁移到 LangChain ChatTongyi，完全 LangChain 化，为后续引入 MCP 做准备。

### 关键约束
- ✅ 完全向后兼容（前端无需修改）
- ✅ 使用 ChatTongyi（继续使用通义千问）
- ✅ MCP 集成仅架构预留，暂不实现
- ✅ 使用 LangChain 链式流式输出

---

## 整体方案：渐进式 LangChain 化

### 阶段划分

```
阶段1: LLM 服务层迁移
├── llm_service.py → 使用 ChatTongyi
├── 保持现有 API 不变
└── 添加 LangChain 消息适配器

阶段2: Agent 节点优化
├── 使用 LangChain PromptTemplate
├── 使用 LangChain Runnable 链
└── 流式输出使用 LangChain astream

阶段3: 架构扩展预留
├── Tool 抽象（为 MCP 预留）
├── Memory 抽象
└── 配置化模型切换
```

---

## 阶段 1: LLM 服务层迁移

### 核心改造：llm_service.py

**before (DashScope SDK)**:
```python
import dashscope
from dashscope import Generation

response = Generation.call(
    model=self.model,
    messages=messages,
    result_format='message',
    temperature=0.7
)
```

**after (LangChain ChatTongyi)**:
```python
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class LLMService:
    def __init__(self):
        self.llm = ChatTongyi(
            model=settings.dashscope_model,
            dashscope_api_key=settings.dashscope_api_key,
            temperature=DEFAULT_TEMPERATURE,
        )

    async def generate_response(self, message, conversation_history, system_prompt=None):
        prompt = self._build_prompt(system_prompt)
        chain = prompt | self.llm | StrOutputParser()
        return await chain.ainvoke({
            "messages": self._convert_messages(conversation_history, message)
        })

    async def generate_response_stream(self, ...):
        async for chunk in chain.astream(...):
            yield chunk
```

### 关键变化
- ✅ ChatTongyi 替换 DashScope SDK
- ✅ 使用 LangChain PromptTemplate
- ✅ 使用 LCEL 链式调用 (`prompt | llm | parser`)
- ✅ 保持现有 API 接口不变

---

## 阶段 2: Agent 节点优化

### 改造 agents/nodes.py

**响应生成节点**:
```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    llm_service = get_llm_service()

    # 使用 ChatPromptTemplate
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_message}")
    ])

    # 构建链
    chain = prompt_template | llm_service.llm | StrOutputParser()

    response = await chain.ainvoke({
        "system_prompt": state.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
        "history": _convert_history(state["conversation_history"]),
        "user_message": state["user_message"]
    })

    return {"response": response}
```

**流式响应节点**:
```python
async def response_generator_node_stream(state: AgentState) -> AsyncIterator[Dict[str, Any]]:
    async for chunk in chain.astream(...):
        yield {"event": "token", "data": {"chunk": chunk}}
```

### 消息格式适配器
```python
def _convert_history(conversation_history: List[Dict]) -> List[BaseMessage]:
    """将现有历史格式转换为 LangChain BaseMessage"""
    messages = []
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages
```

### 关键变化
- ✅ 使用 `ChatPromptTemplate` 替换手动拼接
- ✅ 使用 `MessagesPlaceholder` 处理对话历史
- ✅ 使用 LCEL 链式语法
- ✅ 流式输出使用 `astream` 方法

---

## 阶段 3: 架构扩展预留

### 3.1 Tool 抽象层（MCP 预留）

**新建 app/agents/tools.py**:
```python
from langchain_core.tools import Tool

class ToolRegistry:
    """工具注册中心 - 未来可接入 MCP servers"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, name: str, func: Callable, description: str):
        self._tools[name] = Tool(name=name, func=func, description=description)

    def get_tools(self) -> List[Tool]:
        return list(self._tools.values())

    # 预留 MCP 集成接口
    async def load_from_mcp_server(self, server_url: str):
        """TODO: 实现 MCP protocol 集成"""
        pass
```

### 3.2 Memory 抽象层

**新建 app/agents/memory.py**:
```python
from langchain.memory import ConversationBufferMemory

class MemoryFactory:
    """内存工厂 - 支持多种记忆策略"""

    @staticmethod
    def create_buffer_memory() -> BaseMemory:
        return ConversationBufferMemory(
            return_messages=True,
            output_key="response"
        )

    # 预留：滑动窗口记忆、摘要记忆
```

### 3.3 配置化模型切换

**增强 app/config.py**:
```python
class LLMConfig(BaseSettings):
    provider: str = "tongyi"  # tongyi | openai | anthropic

    # 通义千问配置
    tongyi_model: str = "qwen-max"
    tongyi_api_key: str = ""

    # OpenAI 配置（预留）
    openai_model: str = "gpt-4"
    openai_api_key: str = ""

def create_llm_from_config(config: LLMConfig):
    """根据配置创建 LLM 实例"""
    if config.provider == "tongyi":
        return ChatTongyi(model=config.tongyi_model, ...)
    elif config.provider == "openai":
        return ChatOpenAI(model=config.openai_model, ...)
```

### 目录结构调整
```
backend/app/agents/
├── __init__.py
├── state.py              # 现有 AgentState
├── graph.py              # 现有 workflow
├── nodes.py              # 改造后的节点
├── tools.py              # 新增：工具注册中心
├── memory.py             # 新增：内存抽象
└── prompts.py            # 新增：Prompt 模板管理
```

---

## 兼容性保证

### API 接口保持不变
```python
# llm_service.py 的公共 API 保持不变
async def generate_response(message, conversation_history, system_prompt=None) -> str
async def generate_response_stream(...) -> AsyncIterator[str]
```

### 事件格式兼容
```python
# 流式输出事件格式保持一致
{"event": "start", "data": {...}}
{"event": "token", "data": {"chunk": "..."}}
{"event": "end", "data": {"response": "..."}}
```

---

## 依赖更新

**pyproject.toml**:
```toml
dependencies = [
    "langchain-community>=0.0.10",  # ChatTongyi
    # 保持现有依赖
]
```

---

## 工作量估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 阶段1 | llm_service.py 改造 | 1.5h |
| 阶段1 | 单元测试 | 0.5h |
| 阶段2 | agents/nodes.py 改造 | 1.5h |
| 阶段2 | 流式输出适配 | 1h |
| 阶段3 | Tool/Memory 抽象 | 1h |
| 阶段3 | 配置化改造 | 0.5h |
| 测试 | 端到端测试 | 1h |
| **总计** | | **7h** |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| LangChain API 兼容性问题 | 使用稳定版本，充分测试 |
| 流式输出格式变化 | 添加适配器层保持格式一致 |
| 性能回归 | 迁移前后进行性能对比测试 |

---

## 下一步

使用 `writing-plans` skill 创建详细的实现计划。
