# 服务架构

## Embedding 服务

使用 LangChain 的 `DashScopeEmbeddings` 集成：

```python
from langchain_community.embeddings import DashScopeEmbeddings

embeddings = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key=settings.dashscope_api_key
)
```

**特点:**
- 自动批量处理（内置批量大小的优化）
- 自动重试机制
- 错误处理和降级

## 文本切分服务

使用 LangChain 的 `RecursiveCharacterTextSplitter`：

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", "。", ".", " ", ""],
    chunk_size=1000,
    chunk_overlap=200
)
```

**特点:**
- 递归尝试多种分隔符
- 保持语义完整性
- 可配置的大小和重叠

## LLM 服务

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

**消息转换:**
- LangChain 使用 `HumanMessage`, `AIMessage` 对象
- 提供了 `convert_to_langchain_messages()` 和 `convert_to_dict_messages()` 工具函数
- 支持双向转换，保持与现有系统的兼容性

## 扩展架构

- **ToolRegistry**: 工具注册中心，为 MCP 集成预留
- **MemoryFactory**: 内存管理工厂
- **多提供商支持**: 支持 tongyi、openai 等多种模型
