# LangChain 组件重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 使用 LangChain 的文本切分器和 DashScope Embeddings 集成替换当前自定义实现，解决大文件上传连接问题。

**架构:** 将自定义的 `ChunkingService` 和 `EmbeddingService` 替换为 LangChain 组件。文件处理流程：`File → LangChain TextSplitter → LangChain DashScope Embeddings → ChromaDB`。保持对外接口不变，确保与现有代码兼容。

**技术栈:**
- langchain-community==0.3.14 (DashScope 集成)
- langchain-text-splitters==0.3.6 (文本切分器)
- 现有: dashscope==1.24.3, chromadb==1.5.2, langgraph==1.0.10

---

## Task 1: 添加新依赖

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: 更新 requirements.txt**

在 `backend/requirements.txt` 中添加以下依赖：

```txt
langchain-community==0.3.14
langchain-text-splitters==0.3.6
```

**Step 2: 安装新依赖**

```bash
cd backend
source venv/Scripts/activate
pip install langchain-community==0.3.14 langchain-text-splitters==0.3.6
```

预期输出：成功安装依赖包及其依赖项

**Step 3: 验证安装**

```bash
python -c "from langchain_community.embeddings import DashScopeEmbeddings; from langchain_text_splitters import RecursiveCharacterTextSplitter; print('Import successful')"
```

预期输出：`Import successful`

**Step 4: 提交**

```bash
cd backend
git add requirements.txt
git commit -m "feat: add langchain-community and langchain-text-splitters dependencies"
```

---

## Task 2: 重写 ChunkingService 使用 LangChain

**Files:**
- Modify: `backend/app/services/chunking_service.py`
- Test: `backend/tests/test_chunking_service.py` (创建新测试文件)

**Step 1: 编写失败测试**

创建 `backend/tests/test_chunking_service.py`:

```python
import pytest
from pathlib import Path
import sys
sys.path.insert(0, '.')

from app.services.chunking_service import ChunkingService


def test_chunk_basic_text():
    """测试基本文本切分"""
    service = ChunkingService()
    text = "这是第一段。\n\n这是第二段。\n\n这是第三段。"
    chunks = service.chunk_by_semantic_units(text, "test_doc")

    assert len(chunks) > 0
    assert all("text" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)
    assert all("id" in chunk for chunk in chunks)


def test_chunk_returns_metadata():
    """测试返回的 chunks 包含正确元数据"""
    service = ChunkingService()
    text = "测试文本内容用于验证元数据"
    chunks = service.chunk_by_semantic_units(text, "test_doc")

    for chunk in chunks:
        assert chunk["metadata"]["document_id"] == "test_doc"
        assert "chunk_index" in chunk["metadata"]
        assert isinstance(chunk["metadata"]["chunk_index"], int)


def test_chunk_empty_text():
    """测试空文本处理"""
    service = ChunkingService()
    chunks = service.chunk_by_semantic_units("", "test_doc")
    assert chunks == []


def test_chunk_size_limit():
    """测试 chunk 大小限制"""
    service = ChunkingService(chunk_size=100)
    # 创建一个大于 100 字符的文本
    text = "word" * 50  # 200 字符
    chunks = service.chunk_by_semantic_units(text, "test_doc")

    # 每个 chunk 应该不超过 chunk_size（稍微允许溢出以保持语义完整性）
    for chunk in chunks:
        assert len(chunk["text"]) <= 150  # 允许 50% 溢出
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_chunking_service.py -v
```

预期：测试通过（因为旧实现仍然存在）

**Step 3: 重写 chunking_service.py**

```python
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks using LangChain"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # LangChain RecursiveCharacterTextSplitter
        # 默认分隔符按优先级排序
        default_separators = ["\n\n", "\n", "。", ".", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            separators=separators or default_separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            keep_separator=True  # 保持分隔符以维护语义
        )

    def chunk_text(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata

        Returns:
            List of chunks with text, metadata, and id
        """
        if not text:
            return []

        # 使用 LangChain 切分器
        texts = self.splitter.split_text(text)

        chunks = []
        for idx, chunk_text in enumerate(texts):
            if chunk_text.strip():
                chunks.append({
                    "id": f"{document_id}_chunk_{idx}",
                    "text": chunk_text.strip(),
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": idx,
                        "char_count": len(chunk_text)
                    }
                })

        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    def chunk_by_semantic_units(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text by semantic units (paragraphs)

        For LangChain, we use the same method as chunk_text
        since RecursiveCharacterTextSplitter already handles
        semantic boundaries well.
        """
        return self.chunk_text(text, document_id)


# Singleton
_chunking_service = None


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_chunking_service.py -v
```

预期：所有测试通过

**Step 5: 提交**

```bash
git add app/services/chunking_service.py tests/test_chunking_service.py
git commit -m "refactor: replace custom chunking with LangChain RecursiveCharacterTextSplitter"
```

---

## Task 3: 重写 EmbeddingService 使用 LangChain

**Files:**
- Modify: `backend/app/services/embedding_service.py`
- Test: `backend/tests/test_embedding_service.py` (创建新测试文件)

**Step 1: 编写失败测试**

创建 `backend/tests/test_embedding_service.py`:

```python
import pytest
import sys
sys.path.insert(0, '.')

from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_single_embedding():
    """测试单个文本 embedding"""
    service = EmbeddingService()
    text = "测试文本"
    result = await service.generate_embedding(text)

    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    assert len(result) > 0  # embedding 向量长度


@pytest.mark.asyncio
async def test_batch_embeddings():
    """测试批量 embedding"""
    service = EmbeddingService()
    texts = ["文本1", "文本2", "文本3"]
    results = await service.generate_embeddings_batch(texts)

    assert len(results) == len(texts)
    assert all(isinstance(r, list) for r in results)
    assert all(all(isinstance(x, float) for x in r) for r in results)


@pytest.mark.asyncio
async def test_empty_text_raises_error():
    """测试空文本抛出错误"""
    service = EmbeddingService()
    with pytest.raises(ValueError):
        await service.generate_embedding("")


@pytest.mark.asyncio
async def test_large_batch_handling():
    """测试大批量处理（超过 DashScope 限制）"""
    service = EmbeddingService()
    # 创建 15 个文本，超过 DashScope 批量限制
    texts = [f"测试文本{i}" for i in range(15)]
    results = await service.generate_embeddings_batch(texts)

    assert len(results) == 15
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_embedding_service.py -v
```

预期：旧实现测试通过

**Step 3: 重写 embedding_service.py**

```python
from typing import List
from langchain_community.embeddings import DashScopeEmbeddings
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using LangChain DashScope"""

    def __init__(self):
        settings = get_settings()
        # 使用 LangChain 的 DashScope Embeddings
        self.embeddings = DashScopeEmbeddings(
            model=settings.dashscope_embedding_model,
            dashscope_api_key=settings.dashscope_api_key
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of embedding values

        Raises:
            ValueError: If text is empty or None
        """
        # Input validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # LangChain DashScopeEmbeddings.embed_query 返回 List[float]
        try:
            result = self.embeddings.embed_query(text)
            return result
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            # LangChain DashScopeEmbeddings 自动处理批量
            # 返回 List[List[float]]
            results = self.embeddings.embed_documents(texts)
            return results
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


# Singleton
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_embedding_service.py -v
```

预期：所有测试通过

**Step 5: 提交**

```bash
git add app/services/embedding_service.py tests/test_embedding_service.py
git commit -m "refactor: replace custom embedding with LangChain DashScopeEmbeddings"
```

---

## Task 4: 更新 DocumentService 适配新接口

**Files:**
- Modify: `backend/app/services/document_service.py`
- Test: `backend/tests/test_document_service.py` (更新现有测试)

**Step 1: 验证现有测试**

```bash
cd backend
pytest tests/test_document_service.py -v -k "process_file" 2>&1 | head -50
```

**Step 2: 检查 document_service.py 兼容性**

检查 `document_service.py` 中对 `embedding_service` 的调用是否需要调整。

主要验证：
- `await self.embedding_service.generate_embeddings_batch(texts)` 调用
- 返回类型兼容性

LangChain 的 `embed_documents` 返回 `List[List[float]]`，与原接口一致，应该不需要改动。

**Step 3: 运行完整测试套件**

```bash
cd backend
pytest tests/test_document_service.py -v
pytest tests/test_knowledge_api.py -v
```

预期：所有测试通过

**Step 4: 如果需要，提交兼容性调整**

```bash
git add app/services/document_service.py
git commit -m "refactor: update document service for new embedding interface"
```

---

## Task 5: 端到端测试 - 上传民法典

**Files:**
- Test script: `backend/test_upload.py` (临时测试脚本)

**Step 1: 创建端到端测试脚本**

创建 `backend/test_upload.py`:

```python
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, '.')

from app.services.document_service import DocumentService


async def test_upload():
    """Test uploading the actual 民法典 PDF"""
    service = DocumentService()
    pdf_path = Path('../中华人民共和国民法典_20200528.pdf')

    print(f'Testing upload of: {pdf_path.name}')
    print(f'File size: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB')

    try:
        result = await service.process_file(
            file_path=str(pdf_path),
            title='中华人民共和国民法典',
            category='law',
            source='2020年5月28日'
        )

        print(f'\n✅ Upload successful!')
        print(f'Document ID: {result["document_id"]}')
        print(f'Chunks processed: {result["chunk_count"]}')
        print(f'Category: {result["category"]}')

    except Exception as e:
        print(f'\n❌ Upload failed: {e}')
        raise


if __name__ == "__main__":
    asyncio.run(test_upload())
```

**Step 2: 运行端到端测试**

```bash
cd backend
python test_upload.py
```

预期输出：
```
Testing upload of: 中华人民共和国民法典_20200528.pdf
File size: 2.01 MB
Processing batch 1/XX (10 texts)
...
✅ Upload successful!
Document ID: law_中华人民共和国民法典_xxx
Chunks processed: XXX
Category: law
```

**Step 3: 验证 ChromaDB 存储**

```bash
cd backend
python -c "
from app.services.chroma_service import get_chroma_service
service = get_chroma_service()
stats = await service.get_collection_stats()
print(f'Total documents in collection: {stats[\"count\"]}')
"
```

预期：显示上传的 chunks 数量

**Step 4: 清理测试文件**

```bash
rm backend/test_upload.py
```

**Step 5: 提交**

```bash
git add -A
git commit -m "test: verify large file upload with LangChain components"
```

---

## Task 6: 更新文档

**Files:**
- Create: `backend/docs/ARCHITECTURE.md` (如果不存在则创建)

**Step 1: 更新架构文档**

创建或更新 `backend/docs/ARCHITECTURE.md`:

````markdown
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
````

**Step 2: 提交**

```bash
git add backend/docs/
git commit -m "docs: update architecture documentation for LangChain integration"
```

---

## Task 7: 清理和验证

**Step 1: 运行完整测试套件**

```bash
cd backend
pytest tests/ -v --tb=short
```

预期：所有测试通过

**Step 2: 检查代码风格**

```bash
cd backend
python -m pylint app/services/chunking_service.py app/services/embedding_service.py --disable=C0114,C0115,C0116
```

**Step 3: 验证依赖版本**

```bash
cd backend
pip list | grep -E "langchain|dashscope"
```

预期输出：
```
langchain                 1.2.10
langchain-community       0.3.14
langchain-text-splitters  0.3.6
langgraph                 1.0.10
dashscope                 1.24.3
```

**Step 4: 最终提交**

```bash
git add -A
git commit -m "chore: final cleanup and verification for LangChain refactoring"
```

---

## 总结

**完成后的架构:**

```
File Upload
    ↓
LangChain RecursiveCharacterTextSplitter (chunking_service.py)
    ↓
Chunks (List[str])
    ↓
LangChain DashScopeEmbeddings (embedding_service.py)
    ↓
Embeddings (List[List[float]])
    ↓
ChromaDB Storage (chroma_service.py)
```

**关键改进:**
1. ✅ 使用 LangChain 成熟组件，减少自定义代码
2. ✅ 自动处理批量限制和重试
3. ✅ 更好的文本切分质量
4. ✅ 为 MCP 工具调用做好准备
5. ✅ 代码量减少约 50%

**测试覆盖:**
- 单元测试：chunking_service, embedding_service
- 集成测试：document_service
- 端到端测试：大文件上传
