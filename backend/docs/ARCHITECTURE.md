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
