# Legal Consultation Platform - Complete Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an AI-powered legal consultation platform with chat, RAG-based responses, knowledge base management, and multi-turn conversation support.

**Architecture:** Monolithic FastAPI backend with modular LangGraph agents, React + TypeScript frontend, SQLite (local) with ChromaDB for vectors, OpenAI GPT-4 for LLM.

**Tech Stack:**
- Backend: FastAPI, Python 3.7+, SQLAlchemy, LangChain, LangGraph, OpenAI, ChromaDB
- Frontend: React 18, TypeScript, Vite, TanStack Query, Zustand
- Database: SQLite (local), PostgreSQL (production)
- Vector DB: ChromaDB with OpenAI embeddings

---

## Current Implementation Status

**✅ Completed:**
- Backend project structure with FastAPI
- Database models (Session, Message, KnowledgeDocument)
- Pydantic schemas for all models
- Session and Message CRUD services
- LLM service with OpenAI integration (untested)
- Knowledge API routes (placeholder)
- Chat API with placeholder responses
- Frontend project with Vite + React + TypeScript
- Basic App.tsx component

**🔄 In Progress:**
- OpenAI LLM integration testing

**⏳ Todo:**
- ChromaDB setup and integration
- Document processing and chunking
- RAG retrieval chain
- LangGraph agent orchestrator
- Streaming response support
- Frontend chat components
- Admin knowledge panel
- Tests and documentation

---

## Phase 1: Complete Core Backend Features

### Task 1: Test and Verify OpenAI LLM Integration

**Files:**
- Modify: `backend/app/services/llm_service.py`
- Test: Create `backend/tests/test_llm_service.py`

**Step 1: Configure OpenAI API Key**

Edit `.env` file, replace placeholder:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Step 2: Install required packages**

Run: `cd backend && D:/Python/python.exe -m pip install openai -q`

**Step 3: Create test file**

Create: `backend/tests/test_llm_service.py`

```python
import pytest
import asyncio
from app.services.llm_service import get_llm_service, LLMService

@pytest.mark.asyncio
async def test_llm_service_singleton():
    """Test that LLM service returns singleton instance"""
    service1 = get_llm_service()
    service2 = get_llm_service()
    assert service1 is service2

@pytest.mark.asyncio
async def test_generate_response():
    """Test basic LLM response generation"""
    service = get_llm_service()
    response = await service.generate_response(
        message="你好，请简单介绍一下自己。",
        conversation_history=[]
    )
    assert response is not None
    assert len(response) > 0
    assert "法律" in response or "助手" in response

@pytest.mark.asyncio
async def test_conversation_context():
    """Test that conversation history is used"""
    service = get_llm_service()
    history = [
        {"role": "user", "content": "我叫张三"},
        {"role": "assistant", "content": "你好张三"}
    ]
    response = await service.generate_response(
        message="我叫什么名字？",
        conversation_history=history
    )
    assert "张三" in response
```

**Step 4: Run tests to verify LLM integration**

Run: `cd backend && D:/Python/python.exe -m pytest tests/test_llm_service.py -v`

Expected: PASS (requires valid OpenAI API key)

**Step 5: Update .env.example with API key instructions**

Edit: `backend/.env.example`

Add comment above OPENAI_API_KEY:
```bash
# Get your API key from https://platform.openai.com/api-keys
# Required for LLM features
OPENAI_API_KEY=your_openai_api_key_here
```

**Step 6: Commit**

```bash
git add backend/tests/test_llm_service.py backend/.env.example
git commit -m "test: add LLM service tests and API key documentation"
```

---

### Task 2: Set Up ChromaDB Integration

**Files:**
- Create: `backend/app/services/chroma_service.py`
- Modify: `backend/app/config.py`
- Test: `backend/tests/test_chroma_service.py`

**Step 1: Install ChromaDB**

Run: `cd backend && D:/Python/python.exe -m pip install chromadb -q`

**Step 2: Add ChromaDB settings to config**

Edit: `backend/app/config.py`

After `chroma_db_path` line, add collection name:
```python
# ChromaDB
chroma_db_path: str = "./data/chroma"
chroma_collection_name: str = "legal_knowledge"
chroma_persistent_storage: bool = True
```

**Step 3: Create ChromaDB service**

Create: `backend/app/services/chroma_service.py`

```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class ChromaService:
    """Service for ChromaDB vector operations"""

    def __init__(self):
        settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = settings.chroma_collection_name
        self._collection = None

    @property
    def collection(self):
        """Get or create collection"""
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
            except:
                self._collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Legal knowledge base"}
                )
        return self._collection

    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to collection"""
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            return {
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "distances": results.get("distances", [[]])[0]
            }
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    async def delete_by_document_id(self, document_id: str) -> None:
        """Delete all chunks for a document"""
        try:
            # Get all chunks with this document_id
            results = self.collection.get(
                where={"document_id": document_id}
            )
            if results and results.get("ids"):
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"name": self.collection_name, "count": 0, "metadata": {}}


# Singleton instance
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """Get or create the ChromaDB service singleton"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
```

**Step 4: Create ChromaDB data directory**

Run: `mkdir -p D:/vibe-coding/dialog_chat_room/backend/data/chroma`

**Step 5: Write tests**

Create: `backend/tests/test_chroma_service.py`

```python
import pytest
from app.services.chroma_service import get_chroma_service, ChromaService

@pytest.mark.asyncio
async def test_chroma_singleton():
    """Test singleton pattern"""
    service1 = get_chroma_service()
    service2 = get_chroma_service()
    assert service1 is service2

@pytest.mark.asyncio
async def test_add_documents():
    """Test adding documents"""
    service = get_chroma_service()
    await service.add_documents(
        documents=["Test document 1", "Test document 2"],
        metadatas=[
            {"category": "test", "source": "test1"},
            {"category": "test", "source": "test2"}
        ],
        ids=["test_id_1", "test_id_2"]
    )
    stats = await service.get_collection_stats()
    assert stats["count"] >= 2

@pytest.mark.asyncio
async def test_search_documents():
    """Test searching documents"""
    service = get_chroma_service()
    # This would need embedding service, test structure only
    # embedding = await generate_embedding("test query")
    # results = await service.search(embedding, n_results=2)
    # assert len(results["documents"]) <= 2
```

**Step 6: Run tests**

Run: `cd backend && D:/Python/python.exe -m pytest tests/test_chroma_service.py::test_chroma_singleton -v`

Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/services/chroma_service.py backend/app/config.py backend/tests/test_chroma_service.py
git commit -m "feat: add ChromaDB service for vector storage"
```

---

### Task 3: Implement OpenAI Embedding Service

**Files:**
- Create: `backend/app/services/embedding_service.py`
- Test: `backend/tests/test_embedding_service.py`

**Step 1: Create embedding service**

Create: `backend/app/services/embedding_service.py`

```python
from typing import List
from openai import AsyncOpenAI
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI"""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

**Step 2: Write test**

Create: `backend/tests/test_embedding_service.py`

```python
import pytest
from app.services.embedding_service import get_embedding_service

@pytest.mark.asyncio
async def test_generate_embedding():
    """Test single embedding generation"""
    service = get_embedding_service()
    embedding = await service.generate_embedding("测试文本")
    assert embedding is not None
    assert len(embedding) > 0
    # OpenAI embeddings are 1536 dimensions for text-embedding-3-small
    assert len(embedding) == 1536

@pytest.mark.asyncio
async def test_batch_embeddings():
    """Test batch embedding generation"""
    service = get_embedding_service()
    embeddings = await service.generate_embeddings_batch([
        "文本1", "文本2", "文本3"
    ])
    assert len(embeddings) == 3
    assert all(len(emb) == 1536 for emb in embeddings)
```

**Step 3: Run test**

Run: `cd backend && D:/Python/python.exe -m pytest tests/test_embedding_service.py -v`

Expected: PASS (requires valid API key)

**Step 4: Commit**

```bash
git add backend/app/services/embedding_service.py backend/tests/test_embedding_service.py
git commit -m "feat: add OpenAI embedding service"
```

---

### Task 4: Implement Document Processing and Chunking

**Files:**
- Create: `backend/app/services/document_service.py`
- Create: `backend/app/services/chunking_service.py`
- Test: `backend/tests/test_chunking_service.py`

**Step 1: Install document processing dependencies**

Run: `cd backend && D:/Python/python.exe -m pip install pypdf python-docx -q`

**Step 2: Create chunking service**

Create: `backend/app/services/chunking_service.py`

```python
from typing import List, Dict, Any
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting documents into chunks for embedding"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " ", ""]

    def chunk_text(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata

        Returns:
            List of chunks with text, metadata, and id
        """
        chunks = []
        current_position = 0
        chunk_index = 0

        while current_position < len(text):
            # Find the best split point
            end_position = min(current_position + self.chunk_size, len(text))

            # Try to split at a separator
            split_pos = self._find_split_position(text, current_position, end_position)

            chunk_text = text[current_position:split_pos].strip()

            if chunk_text:
                chunks.append({
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "start_pos": current_position,
                        "end_pos": split_pos
                    }
                })
                chunk_index += 1

            # Move forward with overlap
            current_position = split_pos - self.chunk_overlap
            if current_position < 0:
                current_position = split_pos

        logger.info(f"Split into {len(chunks)} chunks")
        return chunks

    def _find_split_position(self, text: str, start: int, end: int) -> int:
        """Find the best position to split text"""
        if end >= len(text):
            return end

        # Try each separator in order
        for sep in self.separators:
            # Look backwards from end position
            split_pos = text.rfind(sep, start, end)
            if split_pos != -1:
                return split_pos + len(sep)

        # No separator found, return end
        return end

    def chunk_by_semantic_units(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Split text by semantic units (articles, sections, paragraphs)

        Better for legal documents with clear structure
        """
        chunks = []
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\n+', text)

        current_chunk = ""
        chunk_index = 0
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            # If paragraph itself is too long, split it
            if para_len > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, document_id, chunk_index
                    ))
                    chunk_index += 1
                    current_chunk = ""
                    current_length = 0

                # Split long paragraph
                sub_chunks = self.chunk_text(para, document_id)
                chunks.extend(sub_chunks)
                continue

            # Check if adding this paragraph exceeds chunk size
            if current_length + para_len > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, document_id, chunk_index
                ))
                chunk_index += 1
                current_chunk = para
                current_length = para_len
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
                current_length += para_len + (2 if current_chunk != para else 0)

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, document_id, chunk_index
            ))

        return chunks

    def _create_chunk(self, text: str, document_id: str, index: int) -> Dict[str, Any]:
        """Create a chunk dict with metadata"""
        return {
            "id": f"{document_id}_chunk_{index}",
            "text": text,
            "metadata": {
                "document_id": document_id,
                "chunk_index": index,
                "char_count": len(text)
            }
        }


# Singleton
_chunking_service: ChunkingService = None


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service"""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
```

**Step 3: Create document service**

Create: `backend/app/services/document_service.py`

```python
from typing import List, Dict, Any, Optional
from pathlib import Path
import pypdf
import docx
import logging

from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for processing and uploading documents to knowledge base"""

    def __init__(self):
        self.chunking_service = get_chunking_service()
        self.embedding_service = get_embedding_service()
        self.chroma_service = get_chroma_service()

    async def process_file(
        self,
        file_path: str,
        title: str,
        category: str,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a file and add to knowledge base

        Args:
            file_path: Path to the file
            title: Document title
            category: One of 'law', 'case', 'contract', 'interpretation'
            source: Optional source information

        Returns:
            Document info with chunk count
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        # Extract text based on file type
        if suffix == '.pdf':
            text = self._extract_text_from_pdf(path)
        elif suffix == '.docx':
            text = self._extract_text_from_docx(path)
        elif suffix == '.txt':
            text = path.read_text(encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        if not text or len(text.strip()) < 10:
            raise ValueError("Document appears to be empty or too short")

        # Generate document ID
        document_id = f"{category}_{path.stem}_{hash(text)}"

        # Chunk the text
        chunks = self.chunking_service.chunk_by_semantic_units(text, document_id)

        # Generate embeddings for all chunks
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_service.generate_embeddings_batch(texts)

        # Prepare metadata for each chunk
        metadatas = [
            {
                **chunk["metadata"],
                "title": title,
                "category": category,
                "source": source or path.name
            }
            for chunk in chunks
        ]

        # Store in ChromaDB
        ids = [chunk["id"] for chunk in chunks]
        await self.chroma_service.add_documents(texts, metadatas, ids)

        logger.info(f"Processed {path.name}: {len(chunks)} chunks added")

        return {
            "document_id": document_id,
            "title": title,
            "category": category,
            "chunk_count": len(chunks),
            "source": source or path.name
        }

    def _extract_text_from_pdf(self, path: Path) -> str:
        """Extract text from PDF file"""
        try:
            reader = pypdf.PdfReader(path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def _extract_text_from_docx(self, path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text:
                    text_parts.append(para.text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base with semantic query"""
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)

        # Build where filter
        where_filter = {"category": category} if category else None

        # Search ChromaDB
        results = await self.chroma_service.search(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []
        for i, doc in enumerate(results.get("documents", [])):
            metadata = results.get("metadatas", [])[i]
            distance = results.get("distances", [])[i]
            formatted_results.append({
                "text": doc,
                "metadata": metadata,
                "score": 1 - distance,  # Convert distance to similarity score
                "distance": distance
            })

        return formatted_results

    async def delete_document(self, document_id: str) -> None:
        """Delete a document and all its chunks"""
        await self.chroma_service.delete_by_document_id(document_id)
        logger.info(f"Deleted document {document_id}")


# Singleton
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Get or create document service"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
```

**Step 4: Write chunking tests**

Create: `backend/tests/test_chunking_service.py`

```python
import pytest
from app.services.chunking_service import get_chunking_service

def test_basic_chunking():
    """Test basic text chunking"""
    service = get_chunking_service()
    text = "这是一段测试文本。" * 100  # Create a long text
    chunks = service.chunk_text(text, "test_doc")
    assert len(chunks) > 1
    assert all("text" in chunk for chunk in chunks)

def test_semantic_chunking():
    """Test semantic unit chunking"""
    service = get_chunking_service()
    text = """第一段内容。

第二段内容。

第三段内容。""" * 10
    chunks = service.chunk_by_semantic_units(text, "test_doc")
    assert len(chunks) > 0
    # Chunks should preserve paragraph structure
```

**Step 5: Run tests**

Run: `cd backend && D:/Python/python.exe -m pytest tests/test_chunking_service.py -v`

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/document_service.py backend/app/services/chunking_service.py backend/tests/test_chunking_service.py
git commit -m "feat: add document processing and chunking services"
```

---

### Task 5: Implement RAG Retrieval Chain

**Files:**
- Create: `backend/app/services/rag_service.py`
- Test: `backend/tests/test_rag_service.py`

**Step 1: Create RAG service**

Create: `backend/app/services/rag_service.py`

```python
from typing import List, Dict, Any, Optional
from app.services.document_service import get_document_service
from app.services.embedding_service import get_embedding_service
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation"""

    def __init__(self):
        self.document_service = get_document_service()
        self.embedding_service = get_embedding_service()
        self.settings = get_settings()

    async def retrieve_context(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from knowledge base

        Args:
            query: User query
            category: Optional category filter
            top_k: Number of documents to retrieve
            min_score: Minimum similarity score threshold

        Returns:
            List of retrieved documents with metadata
        """
        try:
            results = await self.document_service.search_knowledge(
                query=query,
                category=category,
                n_results=top_k
            )

            # Filter by minimum score
            filtered_results = [
                r for r in results
                if r.get("score", 0) >= min_score
            ]

            logger.info(f"Retrieved {len(filtered_results)} contexts (filtered from {len(results)})")
            return filtered_results

        except Exception as e:
            logger.error(f"Error in RAG retrieval: {e}")
            return []

    def format_context_for_prompt(
        self,
        retrieved_docs: List[Dict[str, Any]]
    ) -> str:
        """
        Format retrieved documents into prompt context

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "未找到相关的法律知识库内容。"

        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc.get("metadata", {})
            title = metadata.get("title", "未知来源")
            category = metadata.get("category", "")
            score = doc.get("score", 0)

            context_parts.append(
                f"[来源 {i}] {title} ({category})\n"
                f"{doc['text']}\n"
                f"相关度: {score:.2f}"
            )

        return "\n\n".join(context_parts)

    async def query_with_rag(
        self,
        query: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform RAG query and return formatted results

        Returns:
            Dict with context string and source references
        """
        retrieved = await self.retrieve_context(query, category)

        return {
            "context": self.format_context_for_prompt(retrieved),
            "sources": [
                {
                    "title": doc.get("metadata", {}).get("title", "未知"),
                    "category": doc.get("metadata", {}).get("category", ""),
                    "score": doc.get("score", 0)
                }
                for doc in retrieved
            ],
            "has_context": len(retrieved) > 0
        }


# Singleton
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
```

**Step 2: Write RAG tests**

Create: `backend/tests/test_rag_service.py`

```python
import pytest
from app.services.rag_service import get_rag_service

@pytest.mark.asyncio
async def test_retrieve_context():
    """Test context retrieval"""
    service = get_rag_service()
    results = await service.retrieve_context("合同法", top_k=3)
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_format_context():
    """Test context formatting"""
    service = get_rag_service()
    docs = [
        {
            "text": "测试文本",
            "metadata": {"title": "测试法", "category": "law"},
            "score": 0.85
        }
    ]
    context = service.format_context_for_prompt(docs)
    assert "测试法" in context
    assert "测试文本" in context
```

**Step 3: Commit**

```bash
git add backend/app/services/rag_service.py backend/tests/test_rag_service.py
git commit -m "feat: add RAG retrieval service"
```

---

### Task 6: Implement Intent Router Agent

**Files:**
- Create: `backend/app/agents/intent_agent.py`
- Test: `backend/tests/test_intent_agent.py`

**Step 1: Create intent agent**

Create: `backend/app/agents/intent_agent.py`

```python
from typing import Dict, Any, Literal
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """User intent categories"""
    LEGAL_CONSULTATION = "legal_consultation"
    GREETING = "greeting"
    CLARIFICATION_NEEDED = "clarification_needed"
    SUMMARY_REQUEST = "summary_request"
    KNOWLEDGE_SEARCH = "knowledge_search"
    GENERAL_CHAT = "general_chat"


class IntentRouterAgent:
    """Agent for classifying user intent"""

    def __init__(self):
        # Define patterns for different intents
        self.greeting_patterns = [
            r"^(你好|您好|hi|hello|嗨|早上好|下午好|晚上好)",
            r"^(你是谁|你是什么|介绍一下自己)"
        ]

        self.summary_patterns = [
            r"(总结|概要|摘要|汇总)",
            r"我们讨论了什么|刚才说了什么"
        ]

        self.clarification_triggers = [
            r"^(是什么|怎么做|怎么办|什么是)",
            r"^.{1,5}$"  # Very short queries
        ]

    async def classify_intent(
        self,
        message: str,
        conversation_history: list
    ) -> Dict[str, Any]:
        """
        Classify user intent from message and context

        Args:
            message: User's message
            conversation_history: Previous messages

        Returns:
            Dict with intent, confidence, and metadata
        """
        message_lower = message.strip().lower()

        # Check for greeting
        if self._match_patterns(message_lower, self.greeting_patterns):
            return {
                "intent": UserIntent.GREETING,
                "confidence": 0.95,
                "needs_rag": False,
                "response_type": "greeting"
            }

        # Check for summary request
        if self._match_patterns(message_lower, self.summary_patterns):
            return {
                "intent": UserIntent.SUMMARY_REQUEST,
                "confidence": 0.9,
                "needs_rag": False,
                "response_type": "summary"
            }

        # Check for clarification need
        if self._match_patterns(message_lower, self.clarification_triggers):
            # Check if context provides enough information
            has_context = len(conversation_history) > 0
            if not has_context or len(message) < 10:
                return {
                    "intent": UserIntent.CLARIFICATION_NEEDED,
                    "confidence": 0.7,
                    "needs_rag": False,
                    "response_type": "clarification",
                    "follow_up": "能否提供更多细节？比如具体的法律问题或场景？"
                }

        # Default to legal consultation (most common)
        # Check if it looks like a legal question
        legal_keywords = [
            "法律", "法", "合同", "侵权", "赔偿", "责任",
            "起诉", "诉讼", "法院", "判决", "法规", "条例",
            "违约", "纠纷", "权益", "义务"
        ]

        has_legal_keyword = any(kw in message for kw in legal_keywords)

        return {
            "intent": UserIntent.LEGAL_CONSULTATION if has_legal_keyword else UserIntent.GENERAL_CHAT,
            "confidence": 0.7 if has_legal_keyword else 0.5,
            "needs_rag": True,
            "response_type": "consultation",
            "query_for_rag": message
        }

    def _match_patterns(self, text: str, patterns: list) -> bool:
        """Check if text matches any of the given patterns"""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


# Singleton
_intent_agent: IntentRouterAgent = None


def get_intent_agent() -> IntentRouterAgent:
    """Get or create intent router agent"""
    global _intent_agent
    if _intent_agent is None:
        _intent_agent = IntentRouterAgent()
    return _intent_agent
```

**Step 2: Write tests**

Create: `backend/tests/test_intent_agent.py`

```python
import pytest
from app.agents.intent_agent import get_intent_agent, UserIntent

@pytest.mark.asyncio
async def test_classify_greeting():
    """Test greeting classification"""
    agent = get_intent_agent()
    result = await agent.classify_intent("你好", [])
    assert result["intent"] == UserIntent.GREETING
    assert result["needs_rag"] is False

@pytest.mark.asyncio
async def test_classify_legal_question():
    """Test legal question classification"""
    agent = get_intent_agent()
    result = await agent.classify_intent("合同违约怎么赔偿？", [])
    assert result["intent"] == UserIntent.LEGAL_CONSULTATION
    assert result["needs_rag"] is True
```

**Step 3: Commit**

```bash
git add backend/app/agents/intent_agent.py backend/tests/test_intent_agent.py
git commit -m "feat: add intent router agent"
```

---

### Task 7: Integrate All Components into Chat Endpoint

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Test: `backend/tests/test_chat_integration.py`

**Step 1: Update chat endpoint with full pipeline**

Edit: `backend/app/api/v1/chat.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.agents.intent_agent import get_intent_agent, UserIntent
from app.schemas.message import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and get a response from the AI with RAG"""
    session_service = SessionService(db)
    message_service = MessageService(db)
    llm_service = get_llm_service()
    rag_service = get_rag_service()
    intent_agent = get_intent_agent()

    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = request.session_id

        # Get conversation history for context
        messages = await message_service.get_messages_by_session(session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    else:
        new_session = await session_service.create_session({"title": None})
        session_id = new_session.id
        conversation_history = []

    try:
        # Classify user intent
        intent_result = await intent_agent.classify_intent(
            message=request.message,
            conversation_history=conversation_history
        )

        # Handle based on intent
        if intent_result["intent"] == UserIntent.GREETING:
            response_content = "你好！我是法律咨询助手。我可以帮助您解答法律相关的问题，包括合同、侵权、劳动争议等方面。请告诉我您需要咨询什么问题？"
            sources = []

        elif intent_result["intent"] == UserIntent.SUMMARY_REQUEST:
            # Generate summary of conversation
            if conversation_history:
                summary_prompt = f"请总结以下对话的主要内容：\n{conversation_history}"
                response_content = await llm_service.generate_response(
                    message=summary_prompt,
                    conversation_history=[],
                    system_prompt="你是一个对话总结助手，请简洁总结对话要点。"
                )
            else:
                response_content = "还没有对话内容可以总结。"
            sources = []

        elif intent_result["intent"] == UserIntent.CLARIFICATION_NEEDED:
            response_content = intent_result.get("follow_up", "能否提供更多细节？")
            sources = []

        else:
            # Legal consultation or general chat - use RAG
            if intent_result.get("needs_rag"):
                rag_result = await rag_service.query_with_rag(
                    query=request.message,
                    category=None
                )

                # Build system prompt with retrieved context
                system_prompt = f"""你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 回答要清晰、易懂，避免过度专业术语
4. 基于提供的法律知识库回答，引用相关法规

参考信息：
{rag_result['context']}

请根据以上参考信息回答用户的问题。如果参考信息不足，请说明这一点。"""

                sources = rag_result.get("sources", [])
            else:
                system_prompt = None
                sources = []

            # Generate response using LLM with context
            response_content = await llm_service.generate_response(
                message=request.message,
                conversation_history=conversation_history,
                system_prompt=system_prompt
            )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in chat: {e}")
        response_content = f"抱歉，处理您的请求时出现错误：{str(e)}"
        sources = []

    # Save the exchange
    await message_service.save_exchange(
        session_id,
        request.message,
        response_content,
        {
            "type": "llm_response",
            "model": llm_service.model,
            "sources": sources,
            "intent": intent_result.get("intent", "general_chat")
        }
    )

    # Update session
    await session_service.increment_message_count(session_id)

    return {
        "session_id": session_id,
        "response": response_content,
        "sources": sources
    }
```

**Step 2: Add missing import**

Add at top of file:
```python
import logging
logger = logging.getLogger(__name__)
```

**Step 3: Create integration test**

Create: `backend/tests/test_chat_integration.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_chat_greeting():
    """Test greeting response"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={
            "message": "你好"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "法律咨询助手" in data["response"]
```

**Step 4: Commit**

```bash
git add backend/app/api/v1/chat.py backend/tests/test_chat_integration.py
git commit -m "feat: integrate RAG and intent router into chat endpoint"
```

---

### Task 8: Add Streaming Response Support

**Files:**
- Create: `backend/app/api/v1/chat_stream.py`
- Test: `backend/tests/test_chat_stream.py`

**Step 1: Create streaming chat endpoint**

Create: `backend/app/api/v1/chat_stream.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from app.database import get_db
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.agents.intent_agent import get_intent_agent
from app.schemas.message import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


async def event_generator(request: ChatRequest, db: AsyncSession):
    """Generate streaming response events"""
    try:
        session_service = SessionService(db)
        message_service = MessageService(db)
        llm_service = get_llm_service()
        rag_service = get_rag_service()
        intent_agent = get_intent_agent()

        # Get or create session
        if request.session_id:
            session = await session_service.get_session(request.session_id)
            if not session:
                yield f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"
                return
            session_id = request.session_id

            messages = await message_service.get_messages_by_session(session_id)
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        else:
            new_session = await session_service.create_session({"title": None})
            session_id = new_session.id
            conversation_history = []

        # Send session ID
        yield f"event: session_id\ndata: {json.dumps({'session_id': session_id})}\n\n"

        # Classify intent
        intent_result = await intent_agent.classify_intent(
            message=request.message,
            conversation_history=conversation_history
        )

        # Handle different intents
        if intent_result["intent"] == "greeting":
            response = "你好！我是法律咨询助手。我可以帮助您解答法律相关的问题。"
            yield f"event: token\ndata: {json.dumps({'token': response})}\n\n"
            yield "event: done\n\n"

            # Save exchange
            await message_service.save_exchange(
                session_id, request.message, response,
                {"type": "greeting", "streaming": True}
            )
            await session_service.increment_message_count(session_id)
            return

        # RAG retrieval for legal queries
        if intent_result.get("needs_rag"):
            rag_result = await rag_service.query_with_rag(request.message)
            sources = rag_result.get("sources", [])

            # Send sources
            yield f"event: sources\ndata: {json.dumps({'sources': sources})}\n\n"

            system_prompt = f"""你是一个专业的法律咨询助手。

参考信息：
{rag_result['context']}

请基于参考信息回答，如果信息不足请说明。"""
        else:
            system_prompt = None
            sources = []

        # Stream LLM response
        full_response = ""
        async for token in llm_service.generate_response_stream(
            message=request.message,
            conversation_history=conversation_history,
            system_prompt=system_prompt
        ):
            full_response += token
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        yield "event: done\n\n"

        # Save after streaming complete
        await message_service.save_exchange(
            session_id, request.message, full_response,
            {"type": "llm_streaming", "sources": sources}
        )
        await session_service.increment_message_count(session_id)

    except Exception as e:
        logger.error(f"Error in streaming chat: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Streaming chat endpoint using Server-Sent Events"""
    return StreamingResponse(
        event_generator(request, db),
        media_type="text/event-stream"
    )
```

**Step 2: Register streaming router**

Edit: `backend/app/api/v1/__init__.py`

```python
from fastapi import APIRouter
from app.api.v1 import sessions, chat, knowledge, chat_stream

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(sessions.router)
api_router.include_router(chat.router)
api_router.include_router(knowledge.router)
api_router.include_router(chat_stream.router)
```

**Step 3: Commit**

```bash
git add backend/app/api/v1/chat_stream.py backend/app/api/v1/__init__.py
git commit -m "feat: add streaming chat endpoint with SSE"
```

---

## Phase 2: Build Frontend Components

### Task 9: Set Up Frontend State Management

**Files:**
- Create: `frontend/src/stores/chatStore.ts`
- Create: `frontend/src/stores/sessionStore.ts`
- Create: `frontend/src/api/client.ts`

**Step 1: Install additional dependencies**

Run: `cd frontend && npm install zustand axios`

**Step 2: Create API client**

Create: `frontend/src/api/client.ts`

```typescript
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatRequest {
  session_id?: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  sources: Array<{
    title: string;
    category: string;
    score: number;
  }>;
}

export const chatApi = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', data);
    return response.data;
  },

  getSessions: async () => {
    const response = await api.get('/sessions');
    return response.data;
  },

  getSession: async (id: string) => {
    const response = await api.get(`/sessions/${id}`);
    return response.data;
  },

  createSession: async () => {
    const response = await api.post('/sessions');
    return response.data;
  },

  deleteSession: async (id: string) => {
    await api.delete(`/sessions/${id}`);
  },
};
```

**Step 3: Create chat store with Zustand**

Create: `frontend/src/stores/chatStore.ts`

```typescript
import { create } from 'zustand';
import { chatApi, ChatRequest } from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Array<{
    title: string;
    category: string;
    score: number;
  }>;
}

interface ChatState {
  sessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;

  sendMessage: (message: string) => Promise<void>;
  setSessionId: (id: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: null,
  messages: [],
  isLoading: false,
  error: null,

  setSessionId: (id) => set({ sessionId: id }),

  clearMessages: () => set({ messages: [], error: null }),

  sendMessage: async (content: string) => {
    set({ isLoading: true, error: null });

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    set((state) => ({ messages: [...state.messages, userMessage] }));

    try {
      const currentSessionId = get().sessionId;
      const response = await chatApi.sendMessage({
        session_id: currentSessionId || undefined,
        message: content,
      });

      // Update session ID if new
      if (!currentSessionId && response.session_id) {
        set({ sessionId: response.session_id });
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        sources: response.sources,
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '发送消息失败',
        isLoading: false,
      });
    }
  },
}));
```

**Step 4: Create session store**

Create: `frontend/src/stores/sessionStore.ts`

```typescript
import { create } from 'zustand';
import { chatApi } from '../api/client';

interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface SessionState {
  sessions: Session[];
  isLoading: boolean;
  error: string | null;

  loadSessions: () => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  isLoading: false,
  error: null,

  loadSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const sessions = await chatApi.getSessions();
      set({ sessions, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '加载会话失败',
        isLoading: false,
      });
    }
  },

  deleteSession: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await chatApi.deleteSession(id);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== id),
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '删除会话失败',
        isLoading: false,
      });
    }
  },
}));
```

**Step 5: Commit**

```bash
cd frontend
git add src/api/client.ts src/stores/chatStore.ts src/stores/sessionStore.ts
git commit -m "feat: add API client and state management with Zustand"
```

---

### Task 10: Create Chat View Component

**Files:**
- Create: `frontend/src/components/chat/ChatView.tsx`
- Create: `frontend/src/components/chat/MessageBubble.tsx`
- Create: `frontend/src/components/chat/MessageInput.tsx`
- Create: `frontend/src/components/chat/CitationBadge.tsx`

**Step 1: Create MessageBubble component**

Create: `frontend/src/components/chat/MessageBubble.tsx`

```typescript
import { Message } from '../../stores/chatStore';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
        isUser
          ? 'bg-blue-500 text-white'
          : 'bg-gray-200 text-gray-800'
      }`}>
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.sources.map((source, idx) => (
              <span
                key={idx}
                className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
              >
                {source.title}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Create MessageInput component**

Create: `frontend/src/components/chat/MessageInput.tsx`

```typescript
import { useState } from 'react';
import { Send } from 'lucide-react';
import { useChatStore } from '../../stores/chatStore';

export function MessageInput() {
  const [message, setMessage] = useState('');
  const { sendMessage, isLoading } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const currentMessage = message;
    setMessage('');
    await sendMessage(currentMessage);
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="输入您的法律问题..."
        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={!message.trim() || isLoading}
        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        <Send className="w-5 h-5" />
      </button>
    </form>
  );
}
```

**Step 3: Create ChatView component**

Create: `frontend/src/components/chat/ChatView.tsx`

```typescript
import { useEffect, useRef } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';

export function ChatView() {
  const { messages, isLoading, error } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">法律咨询助手</h2>
              <p>请输入您的问题，我将为您提供法律信息参考</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-200 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
            {error}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <MessageInput />
    </div>
  );
}
```

**Step 4: Update App.tsx**

Edit: `frontend/src/App.tsx`

```typescript
import { ChatView } from './components/chat/ChatView';

function App() {
  return (
    <div className="App">
      <ChatView />
    </div>
  );
}

export default App;
```

**Step 5: Update CSS for animations**

Edit: `frontend/src/index.css`

```css
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.animate-bounce {
  animation: bounce 1s infinite;
}

.delay-100 {
  animation-delay: 0.1s;
}

.delay-200 {
  animation-delay: 0.2s;
}
```

**Step 6: Commit**

```bash
cd frontend
git add src/components/chat/ src/App.tsx src/index.css
git commit -m "feat: add chat view components"
```

---

### Task 11: Create Session List Sidebar

**Files:**
- Create: `frontend/src/components/common/Sidebar.tsx`
- Create: `frontend/src/components/common/SessionList.tsx`

**Step 1: Create SessionList component**

Create: `frontend/src/components/common/SessionList.tsx`

```typescript
import { useEffect } from 'react';
import { Trash2, MessageSquare } from 'lucide-react';
import { useSessionStore } from '../../stores/sessionStore';
import { useChatStore } from '../../stores/chatStore';

export function SessionList() {
  const { sessions, isLoading, loadSessions, deleteSession } = useSessionStore();
  const { sessionId, setSessionId, clearMessages } = useChatStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleSelectSession = (id: string) => {
    setSessionId(id);
    clearMessages();
  };

  const handleNewChat = () => {
    setSessionId(null);
    clearMessages();
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('确定删除此会话吗？')) {
      await deleteSession(id);
      if (sessionId === id) {
        handleNewChat();
      }
    }
  };

  return (
    <div className="w-64 border-r flex flex-col bg-gray-50">
      <div className="p-4 border-b">
        <button
          onClick={handleNewChat}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          + 新对话
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-500">加载中...</div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">暂无会话</div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => handleSelectSession(session.id)}
              className={`p-4 border-b cursor-pointer hover:bg-gray-100 flex justify-between items-center ${
                sessionId === session.id ? 'bg-blue-100' : ''
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">
                  {session.title || '新对话'}
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-1">
                  <MessageSquare className="w-3 h-3" />
                  {session.message_count} 条消息
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(e, session.id)}
                className="p-1 hover:text-red-500"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

**Step 2: Update App.tsx with sidebar**

Edit: `frontend/src/App.tsx`

```typescript
import { ChatView } from './components/chat/ChatView';
import { SessionList } from './components/common/SessionList';

function App() {
  return (
    <div className="App flex h-screen">
      <SessionList />
      <div className="flex-1">
        <ChatView />
      </div>
    </div>
  );
}

export default App;
```

**Step 3: Commit**

```bash
cd frontend
git add src/components/common/ src/App.tsx
git commit -m "feat: add session list sidebar"
```

---

## Phase 3: Knowledge Base Admin (Optional)

### Task 12: Create Admin Upload Component

**Files:**
- Create: `frontend/src/components/admin/DocumentUpload.tsx`
- Create: `frontend/src/api/knowledge.ts`

**Step 1: Create knowledge API**

Create: `frontend/src/api/knowledge.ts`

```typescript
import { api } from './client';

export const knowledgeApi = {
  uploadDocument: async (file: File, title: string, category: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('category', category);

    const response = await api.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getDocuments: async () => {
    const response = await api.get('/knowledge');
    return response.data;
  },

  deleteDocument: async (id: string) => {
    await api.delete(`/knowledge/${id}`);
  },
};
```

**Step 2: Create DocumentUpload component**

Create: `frontend/src/components/admin/DocumentUpload.tsx`

```typescript
import { useState, useRef } from 'react';
import { Upload } from 'lucide-react';
import { knowledgeApi } from '../../api/knowledge';

export function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState<'law' | 'case' | 'contract' | 'interpretation'>('law');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      await knowledgeApi.uploadDocument(file, title || file.name, category);
      alert('文档上传成功！');
      setFile(null);
      setTitle('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      alert('上传失败：' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 border rounded-lg">
      <h3 className="font-semibold">上传知识文档</h3>

      <div>
        <label className="block text-sm font-medium mb-1">选择文件</label>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="w-full border rounded p-2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">标题</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="文档标题（可选）"
          className="w-full border rounded p-2"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">分类</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as any)}
          className="w-full border rounded p-2"
        >
          <option value="law">法律法规</option>
          <option value="case">案例</option>
          <option value="contract">合同</option>
          <option value="interpretation">司法解释</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={!file || uploading}
        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
      >
        {uploading ? '上传中...' : <><Upload className="w-4 h-4 inline mr-2" />上传文档</>}
      </button>
    </form>
  );
}
```

**Step 3: Commit**

```bash
cd frontend
git add src/components/admin/ src/api/knowledge.ts
git commit -m "feat: add document upload component for admin"
```

---

## Phase 4: Testing & Documentation

### Task 13: Create Comprehensive Tests

**Files:**
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_e2e.py`

**Step 1: Create test configuration**

Create: `backend/tests/conftest.py`

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import session, message, knowledge

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def test_db():
    """Create a test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    testing_session_local = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with testing_session_local() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def test_client(test_db):
    """Create a test client with test database"""
    from fastapi.testclient import TestClient
    from app.main import app

    async def override_get_db():
        yield test_db

    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
```

**Step 2: Create end-to-end test**

Create: `backend/tests/test_e2e.py`

```python
import pytest

def test_chat_flow(test_client):
    """Test complete chat flow"""
    # Create new session with message
    response = test_client.post("/api/v1/chat", json={
        "message": "你好"
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "response" in data

    session_id = data["session_id"]

    # Continue conversation
    response = test_client.post("/api/v1/chat", json={
        "session_id": session_id,
        "message": "合同法的基本原则是什么？"
    })
    assert response.status_code == 200

    # Get session history
    response = test_client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message_count"] >= 2

def test_session_crud(test_client):
    """Test session CRUD operations"""
    # List sessions
    response = test_client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Step 3: Run all tests**

Run: `cd backend && D:/Python/python.exe -m pytest tests/ -v`

**Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_e2e.py
git commit -m "test: add comprehensive test suite"
```

---

### Task 14: Create Documentation

**Files:**
- Create: `README.md`
- Create: `DEPLOYMENT.md`
- Create: `backend/requirements.txt`

**Step 1: Create main README**

Create: `D:\vibe-coding\dialog_chat_room\README.md`

```markdown
# Legal Consultation Platform

AI-powered legal consultation platform with RAG-based responses.

## Features

- Multi-turn legal consultation chat
- Context-aware conversations
- Knowledge base with vector search (ChromaDB)
- Session management
- Admin panel for knowledge base management

## Tech Stack

- **Backend:** FastAPI, Python, LangChain, OpenAI GPT-4
- **Frontend:** React, TypeScript, Vite
- **Database:** SQLite (local), PostgreSQL (production)
- **Vector DB:** ChromaDB
- **Embeddings:** OpenAI text-embedding-3-small

## Quick Start

### Backend

1. Configure environment:
```bash
cd backend
cp .env.example .env
# Edit .env with your OpenAI API key
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run database migrations:
```bash
python create_tables.py
```

4. Start server:
```bash
uvicorn app.main:app --reload
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start dev server:
```bash
npm run dev
```

3. Open http://localhost:5173

## Environment Variables

See `.env.example` for required variables.

## API Documentation

Start the backend and visit http://localhost:8000/docs

## Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

## License

MIT
```

**Step 2: Create requirements.txt**

Create: `backend/requirements.txt`

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
aiosqlite==0.19.0
alembic==1.13.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
langchain==0.1.0
langgraph==0.0.2
openai==1.3.0
chromadb==0.4.18
pypdf==3.17.0
python-docx==1.1.0
structlog==23.2.0
```

**Step 3: Commit**

```bash
git add README.md DEPLOYMENT.md backend/requirements.txt
git commit -m "docs: add project documentation"
```

---

## Execution Summary

**Total Tasks:** 14
**Estimated Time:** 4-6 hours
**Files Modified:** ~30 files
**Files Created:** ~25 files

**Dependencies Required:**
- Backend: `chromadb`, `pypdf`, `python-docx`, `openai`, `langchain`, `langgraph`
- Frontend: `zustand`, `axios`, `lucide-react`

**Key Implementation Points:**
1. OpenAI API key required for LLM features
2. ChromaDB persists to `./data/chroma`
3. Streaming responses use Server-Sent Events
4. Frontend uses Zustand for state management
5. All API calls go through centralized client

---

**Plan complete and saved to `docs/plans/2026-03-08-legal-consultation-implementation.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
