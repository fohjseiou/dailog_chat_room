# LangGraph 编排重构设计

## 概述

将当前手动执行节点的方式重构为使用 LangGraph 的 `ainvoke()` 和 `astream()` 进行真正的流程编排，解决无法轻松扩展多 Agent 的问题。

**日期**: 2026-03-11
**状态**: 已批准
**方案**: 方案 A - 统一 Graph + 流式配置

---

## 问题陈述

当前实现中，`chat.py` 手动依次调用节点函数，而非使用 LangGraph 的编排能力：

```python
# 当前实现（错误）
intent_result = await intent_router_node(state)
state.update(intent_result)
if intent_result.get("user_intent") == "legal_consultation":
    rag_result = await rag_retriever_node(state)
    state.update(rag_result)
response_result = await response_generator_node(state)
```

这导致：
1. Graph 定义被架空，失去编排能力
2. 添加新 Agent 需要修改 API 层代码
3. 流式/非流式逻辑重复

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                           │
│  (chat.py - 只负责 HTTP/HTTP2 协议处理，SSE 格式转换)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph Orchestration                │
│                                                               │
│   START                                                      │
│     │                                                        │
│     ▼                                                        │
│   ┌──────────────┐     ┌─────────────────────────────────┐ │
│   │intent_router │ ───▶│  Conditional Edge (route_by_     │ │
│   └──────────────┘     │   intent)                        │ │
│                        │  - greeting → response           │ │
│                        │  - legal → rag → response        │ │
│                        │  - doc → doc_agent → response    │ │
│                        │  - general → response            │ │
│                        └─────────────────────────────────┘ │
│                                     │                       │
│                                     ▼                       │
│                        ┌─────────────────────────────┐     │
│                        │   response_generator        │     │
│                        │   (统一处理流式/非流式)      │     │
│                        └──────────────┬──────────────┘     │
│                                       │                    │
│                                       ▼                    │
│                        ┌─────────────────────────────┐     │
│                        │   memory_extraction         │     │
│                        │   (可选，仅认证用户)         │     │
│                        └──────────────┬──────────────┘     │
│                                       │                    │
│                                       ▼                    │
│                                     END                    │
└─────────────────────────────────────────────────────────────┘
```

### 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| Graph 数量 | 单一 Graph | 减少维护，共享逻辑 |
| 流式控制 | State 参数 | 运行时控制，无需多 Graph |
| 路由方式 | 条件边函数 | 灵活，易于扩展新 Agent |
| 记忆提取 | 后处理节点 | 与响应生成解耦，易于测试 |

---

## Graph 结构

### 节点列表

| 节点 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `intent_router` | 意图分类 | `user_message` | `user_intent` |
| `rag_retriever` | RAG 检索 | `user_intent`, `user_message` | `context_str`, `sources` |
| `doc_analyzer` | 文档分析 | `user_message` | `doc_analysis` (未来) |
| `response_generator` | 生成响应 | 全部 state | `response` |
| `memory_extraction` | 记忆提取 | `user_id`, `conversation_history` | `memory_extracted` |

### 边定义

```python
START → intent_router

intent_router → (条件) →
    ├─ greeting → response_generator
    ├─ legal_consultation → rag_retriever → response_generator
    ├─ document_analysis → doc_analyzer → response_generator
    └─ general_chat → response_generator

response_generator → (条件) →
    ├─ [有 user_id] → memory_extraction → END
    └─ [无 user_id] → END
```

---

## 状态定义

```python
class AgentState(TypedDict):
    # 输入
    user_message: str
    conversation_history: List[Dict[str, str]]

    # 控制参数
    streaming: bool  # 是否启用流式模式
    user_id: Optional[str]
    session_id: Optional[str]  # 用于记忆提取

    # 流程状态
    user_intent: str

    # RAG 相关
    retrieved_context: Optional[List[Dict[str, Any]]]
    context_str: Optional[str]
    sources: Optional[List[Dict[str, Any]]]

    # 输出
    response: Optional[str]
    streaming_output: Optional[AsyncIterator]  # 流式输出
    error: Optional[str]

    # 记忆相关
    memory_extracted: Optional[bool]
    facts_extracted: Optional[List[str]]
    summary_generated: Optional[str]
```

---

## 节点设计

### response_generator_node

通过 `state["streaming"]` 决定输出模式：

```python
async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    """统一的响应生成节点"""
    if state.get("streaming", False):
        return await _generate_streaming_response(state)
    else:
        return await _generate_regular_response(state)
```

### memory_extraction_node (新增)

```python
async def memory_extraction_node(state: AgentState) -> Dict[str, Any]:
    """记忆提取节点 - 仅对认证用户执行"""
    user_id = state.get("user_id")

    if not user_id:
        return {"memory_extracted": False}

    # 执行记忆提取逻辑
    # ...
```

---

## API 层集成

### 非流式接口

```python
@router.post("")
async def chat(request: ChatRequest, ...):
    # 1. 准备状态
    state = create_initial_state(..., streaming=False)

    # 2. 执行 Graph
    agent_graph = get_unified_agent_graph()
    final_state = await agent_graph.ainvoke(state)

    # 3. 返回结果
    return {"response": final_state.get("response")}
```

### 流式接口

```python
@router.post("/stream")
async def chat_stream(request: ChatRequest, ...):
    async def stream_events():
        state = create_initial_state(..., streaming=True)
        agent_graph = get_unified_agent_graph()

        async for event in agent_graph.astream(state):
            # 转换为 SSE 事件
            for node_name, output in event.items():
                yield _format_sse(node_name, output)

    return StreamingResponse(stream_events(), media_type="text/event-stream")
```

---

## 扩展性：添加新 Agent

### 步骤

1. **在 `nodes.py` 添加节点函数** (~20 行)
2. **更新意图识别** (1 行)
3. **更新 Graph 边定义** (3 行)

### 示例：添加文档分析 Agent

```python
# 1. 新节点
async def doc_analyzer_node(state: AgentState) -> Dict[str, Any]:
    # 分析文档逻辑
    return {"doc_analysis": result}

# 2. 意图识别更新
if any(kw in message for kw in ["文档", "文件"]):
    return {"user_intent": "document_analysis"}

# 3. Graph 更新
workflow.add_node("doc_analyzer", doc_analyzer_node)
workflow.add_conditional_edges("intent_router", ...,
    {"document_analysis": "doc_analyzer", ...})
workflow.add_edge("doc_analyzer", "response_generator")
```

**总计**: ~24 行代码，无需修改 API 层

---

## 文件变更

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `backend/app/agents/graph.py` | 重构 | 使用统一 Graph，添加 memory_extraction 节点 |
| `backend/app/agents/state.py` | 更新 | 添加 streaming, session_id 等字段 |
| `backend/app/agents/nodes.py` | 更新 | 添加 memory_extraction_node，更新 response_generator_node |
| `backend/app/api/v1/chat.py` | 简化 | 使用 ainvoke/astream，移除手动节点调用 |
| `backend/tests/agents/` | 新增 | Graph 执行测试 |

---

## 测试策略

### 单元测试

- 测试每个节点的输入输出
- 测试条件边路由逻辑

### 集成测试

- 测试完整 Graph 执行（非流式）
- 测试流式输出事件序列

### 端到端测试

- 测试 API 接口
- 测试多 Agent 路由

---

## 后续优化

- [ ] 支持子 Graph 模式（更复杂的 Agent 协作）
- [ ] 添加 Graph 可视化
- [ ] 支持 Agent 并行执行
