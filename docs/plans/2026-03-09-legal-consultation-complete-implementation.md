# 法律咨询助手平台 - 完整实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成基于阿里云 DashScope Qwen + LangChain/LangGraph 的 AI 法律咨询平台，支持多轮对话、RAG 知识库检索、会话管理和知识库管理功能。

**Architecture:** FastAPI 后端 + LangGraph Agent 编排，React + TypeScript 前端，SQLite 本地数据库，ChromaDB 向量存储，DashScope Qwen LLM 和 Embeddings。

**Tech Stack:**
- Backend: FastAPI, Python 3.7+, SQLAlchemy, LangChain, LangGraph, DashScope SDK
- Frontend: React 18, TypeScript, Vite, Zustand, TanStack Query
- Database: SQLite (本地开发), PostgreSQL (生产环境)
- Vector DB: ChromaDB with DashScope text-embedding-v3
- LLM: Alibaba DashScope Qwen (qwen-plus/qwen-turbo)

---

## 当前实现状态

**✅ 已完成:**
- Backend 项目结构和 FastAPI 配置
- 数据库模型 (Session, Message, KnowledgeDocument)
- Pydantic schemas
- Session 和 Message CRUD 服务
- LLM 服务 (DashScope Qwen 集成)
- Embedding 服务 (DashScope text-embedding-v3)
- ChromaDB 向量存储服务
- 文档处理服务 (PDF/DOCX/TXT)
- 文本分块服务
- LangGraph agent 结构 (Intent Router, RAG Retriever, Response Generator)
- 聊天 API 端点
- 基础测试框架
- Frontend 项目 (React + TypeScript + Vite)
- ChatView 和 SessionList 组件
- API client 和 Zustand 状态管理

**🔄 需要完善:**
- 知识库管理 API (目前是占位符)
- 流式响应支持
- 会话摘要生成功能
- 管理员知识库面板前端
- 完整的测试覆盖

**⏳ 待实现:**
- 知识库文档 CRUD API
- 前端知识库管理界面
- 文档上传处理
- 流式聊天响应
- 会话自动摘要
- 前端样式优化

---

## Phase 1: 完善后端知识库管理 API

### Task 1: 实现知识库文档列表 API

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`
- Test: `backend/tests/test_knowledge_api.py`

**Step 1: 编写失败的测试**

```python
# tests/test_knowledge_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_knowledge_documents():
    """Test listing all knowledge documents"""
    response = client.get("/api/v1/knowledge/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_knowledge_api.py::test_list_knowledge_documents -v
```

Expected: FAIL with 404 or undefined endpoint

**Step 3: 实现列表 API 端点**

```python
# app/api/v1/knowledge.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.knowledge import KnowledgeDocumentResponse, KnowledgeDocumentListResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List all knowledge documents with optional category filter"""
    service = KnowledgeService(db)
    documents = await service.list_documents(category=category)
    return {"documents": documents}
```

**Step 4: 创建 KnowledgeService**

```python
# app/services/knowledge_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import KnowledgeDocumentResponse
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_documents(self, category: Optional[str] = None) -> List[KnowledgeDocumentResponse]:
        """List knowledge documents with optional category filter"""
        query = select(KnowledgeDocument)

        if category:
            query = query.where(KnowledgeDocument.category == category)

        query = query.order_by(KnowledgeDocument.created_at.desc())

        result = await self.db.execute(query)
        documents = result.scalars().all()

        return [
            KnowledgeDocumentResponse(
                id=str(doc.id),
                title=doc.title,
                category=doc.category,
                source=doc.source,
                chunk_count=doc.chunk_count,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat()
            )
            for doc in documents
        ]

    async def get_document(self, document_id: str) -> Optional[KnowledgeDocumentResponse]:
        """Get a single document by ID"""
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()

        if not doc:
            return None

        return KnowledgeDocumentResponse(
            id=str(doc.id),
            title=doc.title,
            category=doc.category,
            source=doc.source,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat()
        )

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from database"""
        from app.services.document_service import get_document_service

        # First delete from ChromaDB
        doc_service = get_document_service()
        await doc_service.delete_document(document_id)

        # Then delete from database
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()

        if doc:
            await self.db.delete(doc)
            await self.db.commit()
            logger.info(f"Deleted document {document_id}")
            return True

        return False
```

**Step 5: 更新 schemas**

```python
# app/schemas/knowledge.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    category: Optional[str]
    source: Optional[str]
    chunk_count: int
    created_at: str
    updated_at: str


class KnowledgeDocumentListResponse(BaseModel):
    documents: List[KnowledgeDocumentResponse]


class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: str  # law, case, contract, interpretation
    source: Optional[str] = None
```

**Step 6: 运行测试验证通过**

```bash
cd backend
pytest tests/test_knowledge_api.py::test_list_knowledge_documents -v
```

Expected: PASS

**Step 7: 提交**

```bash
cd backend
git add app/api/v1/knowledge.py app/services/knowledge_service.py app/schemas/knowledge.py tests/test_knowledge_api.py
git commit -m "feat: add knowledge documents list API"
```

---

### Task 2: 实现文档上传 API

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`
- Test: `backend/tests/test_knowledge_api.py`

**Step 1: 编写失败的测试**

```python
def test_upload_document():
    """Test uploading a document"""
    # Create a test text file
    with open("test_legal_doc.txt", "w", encoding="utf-8") as f:
        f.write("这是测试法律文档。\n\n包含一些法律条款内容。")

    with open("test_legal_doc.txt", "rb") as f:
        response = client.post(
            "/api/v1/knowledge/upload",
            files={"file": ("test_legal_doc.txt", f, "text/plain")},
            data={
                "title": "测试法律文档",
                "category": "law"
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["title"] == "测试法律文档"
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_knowledge_api.py::test_upload_document -v
```

Expected: FAIL with 404 or undefined endpoint

**Step 3: 实现上传 API 端点**

```python
# app/api/v1/knowledge.py (add to existing)
from fastapi import UploadFile, File, Form
from app.services.document_service import get_document_service
from app.models.knowledge import KnowledgeDocument
import tempfile
import os
from pathlib import Path


@router.post("/upload", response_model=KnowledgeDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    source: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document into the knowledge base"""

    # Validate category
    if category not in KnowledgeDocument.VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {KnowledgeDocument.VALID_CATEGORIES}"
        )

    # Save uploaded file to temp location
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Process the document
        doc_service = get_document_service()
        result = await doc_service.process_file(
            file_path=temp_file_path,
            title=title,
            category=category,
            source=source
        )

        # Save to database
        from sqlalchemy import insert
        doc = KnowledgeDocument(
            id=result["document_id"],
            title=result["title"],
            category=result["category"],
            source=result["source"],
            chunk_count=result["chunk_count"]
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        return KnowledgeDocumentResponse(
            id=str(doc.id),
            title=doc.title,
            category=doc.category,
            source=doc.source,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat()
        )

    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_knowledge_api.py::test_upload_document -v
```

Expected: PASS

**Step 5: 提交**

```bash
cd backend
git add app/api/v1/knowledge.py tests/test_knowledge_api.py
git commit -m "feat: add document upload API"
```

---

### Task 3: 实现文档删除 API

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`
- Test: `backend/tests/test_knowledge_api.py`

**Step 1: 编写失败的测试**

```python
def test_delete_document():
    """Test deleting a document"""
    # First create a document
    with open("test_delete_doc.txt", "w", encoding="utf-8") as f:
        f.write("待删除的文档内容")

    with open("test_delete_doc.txt", "rb") as f:
        upload_response = client.post(
            "/api/v1/knowledge/upload",
            files={"file": ("test_delete_doc.txt", f, "text/plain")},
            data={"title": "删除测试", "category": "law"}
        )

    document_id = upload_response.json()["document_id"]

    # Delete it
    response = client.delete(f"/api/v1/knowledge/documents/{document_id}")
    assert response.status_code == 200

    # Verify it's gone
    list_response = client.get("/api/v1/knowledge/documents")
    documents = list_response.json()["documents"]
    assert not any(d["id"] == document_id for d in documents)
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_knowledge_api.py::test_delete_document -v
```

Expected: FAIL with 404

**Step 3: 实现删除 API 端点**

```python
# app/api/v1/knowledge.py (add to existing)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document from knowledge base"""
    service = KnowledgeService(db)
    success = await service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted successfully"}
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_knowledge_api.py::test_delete_document -v
```

Expected: PASS

**Step 5: 提交**

```bash
cd backend
git add app/api/v1/knowledge.py tests/test_knowledge_api.py
git commit -m "feat: add document delete API"
```

---

## Phase 2: 实现流式响应支持

### Task 4: 添加流式聊天 API 端点

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_chat_streaming.py`

**Step 1: 编写失败的测试**

```python
# tests/test_chat_streaming.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_streaming():
    """Test streaming chat response"""
    response = client.post("/api/v1/chat/stream", json={
        "message": "你好，请介绍一下自己"
    })

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    # Consume the stream
    lines = response.text.split("\n")
    assert len(lines) > 0
    assert any("data:" in line for line in lines)
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_chat_streaming.py::test_chat_streaming -v
```

Expected: FAIL with 404

**Step 3: 实现流式端点**

```python
# app/api/v1/chat.py (add new endpoint)
from fastapi.responses import StreamingResponse
from app.services.llm_service import get_llm_service


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """Send a message and get a streaming response"""

    async def generate():
        session_service = SessionService(db)
        message_service = MessageService(db)
        llm_service = get_llm_service()

        # Get or create session
        if request.session_id:
            session = await session_service.get_session(request.session_id)
            if not session:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                return
            session_id = request.session_id
            messages = await message_service.get_messages_by_session(session_id)
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages[-10:]
            ]
        else:
            new_session = await session_service.create_session({"title": None})
            session_id = new_session.id
            conversation_history = []

        # Send session ID first
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': str(session_id)})}\n\n"

        # Generate streaming response
        full_response = ""
        async for chunk in llm_service.generate_response_stream(
            message=request.message,
            conversation_history=conversation_history
        ):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        # Save the exchange
        await message_service.save_exchange(
            session_id,
            request.message,
            full_response,
            {"type": "streaming_response"}
        )
        await session_service.increment_message_count(session_id)

        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_chat_streaming.py::test_chat_streaming -v
```

Expected: PASS

**Step 5: 提交**

```bash
cd backend
git add app/api/v1/chat.py tests/test_chat_streaming.py
git commit -m "feat: add streaming chat endpoint"
```

---

## Phase 3: 实现前端知识库管理界面

### Task 5: 创建知识库管理页面组件

**Files:**
- Create: `frontend/src/components/knowledge/KnowledgePanel.tsx`
- Create: `frontend/src/components/knowledge/DocumentList.tsx`
- Create: `frontend/src/components/knowledge/UploadModal.tsx`

**Step 1: 创建 API 客户端方法**

```typescript
// src/api/client.ts (add to existing)

export interface KnowledgeDocument {
  id: string;
  title: string;
  category: string | null;
  source: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeListResponse {
  documents: KnowledgeDocument[];
}

export const knowledgeApi = {
  getDocuments: async (category?: string): Promise<KnowledgeListResponse> => {
    const params = category ? { category } : {};
    const response = await api.get<KnowledgeListResponse>('/knowledge/documents', { params });
    return response.data;
  },

  uploadDocument: async (file: File, title: string, category: string, source?: string): Promise<KnowledgeDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('category', category);
    if (source) formData.append('source', source);

    const response = await api.post<KnowledgeDocument>('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  deleteDocument: async (id: string) => {
    await api.delete(`/knowledge/documents/${id}`);
  },
};
```

**Step 2: 创建知识库 Store**

```typescript
// src/stores/knowledgeStore.ts
import { create } from 'zustand';
import { knowledgeApi, KnowledgeDocument } from '../api/client';

interface KnowledgeState {
  documents: KnowledgeDocument[];
  isLoading: boolean;
  error: string | null;
  isUploading: boolean;

  fetchDocuments: (category?: string) => Promise<void>;
  uploadDocument: (file: File, title: string, category: string, source?: string) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  documents: [],
  isLoading: false,
  error: null,
  isUploading: false,

  fetchDocuments: async (category) => {
    set({ isLoading: true, error: null });
    try {
      const response = await knowledgeApi.getDocuments(category);
      set({ documents: response.documents, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '加载知识库失败',
        isLoading: false
      });
    }
  },

  uploadDocument: async (file, title, category, source) => {
    set({ isUploading: true, error: null });
    try {
      await knowledgeApi.uploadDocument(file, title, category, source);
      // Refresh the list
      await get().fetchDocuments();
      set({ isUploading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '上传文档失败',
        isUploading: false
      });
    }
  },

  deleteDocument: async (id) => {
    set({ error: null });
    try {
      await knowledgeApi.deleteDocument(id);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== id)
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : '删除文档失败'
      });
    }
  },
}));
```

**Step 3: 创建文档列表组件**

```tsx
// src/components/knowledge/DocumentList.tsx
import { useKnowledgeStore } from '../../stores/knowledgeStore';

const CATEGORIES = {
  law: '法律法规',
  case: '案例',
  contract: '合同',
  interpretation: '司法解释'
};

export function DocumentList() {
  const { documents, isLoading, error, deleteDocument } = useKnowledgeStore();

  if (isLoading) {
    return <div className="p-4 text-center">加载中...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (documents.length === 0) {
    return <div className="p-4 text-center text-gray-500">暂无文档</div>;
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div key={doc.id} className="border rounded-lg p-4 flex justify-between items-center">
          <div>
            <h3 className="font-semibold">{doc.title}</h3>
            <p className="text-sm text-gray-500">
              {doc.category && CATEGORIES[doc.category]} • {doc.chunk_count} 个片段
            </p>
          </div>
          <button
            onClick={() => deleteDocument(doc.id)}
            className="text-red-500 hover:text-red-700"
          >
            删除
          </button>
        </div>
      ))}
    </div>
  );
}
```

**Step 4: 创建上传模态框**

```tsx
// src/components/knowledge/UploadModal.tsx
import { useState } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';

interface UploadModalProps {
  onClose: () => void;
}

export function UploadModal({ onClose }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('law');
  const [source, setSource] = useState('');
  const { uploadDocument, isUploading } = useKnowledgeStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    await uploadDocument(file, title, category, source || undefined);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">上传文档</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">文件</label>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full border rounded p-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">标题</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border rounded p-2"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">分类</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border rounded p-2"
            >
              <option value="law">法律法规</option>
              <option value="case">案例</option>
              <option value="contract">合同</option>
              <option value="interpretation">司法解释</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">来源（可选）</label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full border rounded p-2"
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded"
              disabled={isUploading}
            >
              取消
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
              disabled={isUploading}
            >
              {isUploading ? '上传中...' : '上传'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

**Step 5: 创建知识库面板组件**

```tsx
// src/components/knowledge/KnowledgePanel.tsx
import { useEffect, useState } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { DocumentList } from './DocumentList';
import { UploadModal } from './UploadModal';

export function KnowledgePanel() {
  const { fetchDocuments } = useKnowledgeStore();
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <h2 className="text-lg font-bold">知识库管理</h2>
        <button
          onClick={() => setShowUpload(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          上传文档
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <DocumentList />
      </div>
      {showUpload && <UploadModal onClose={() => setShowUpload(false)} />}
    </div>
  );
}
```

**Step 6: 更新 App.tsx 添加导航**

```tsx
// src/App.tsx
import { useState } from 'react';
import { ChatView } from './components/chat/ChatView';
import { SessionList } from './components/common/SessionList';
import { KnowledgePanel } from './components/knowledge/KnowledgePanel';

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'knowledge'>('chat');

  return (
    <div className="App flex h-screen">
      <div className="w-64 border-r">
        <div className="p-4 border-b">
          <nav className="flex space-x-2">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1 rounded ${
                activeTab === 'chat' ? 'bg-blue-500 text-white' : 'bg-gray-200'
              }`}
            >
              聊天
            </button>
            <button
              onClick={() => setActiveTab('knowledge')}
              className={`px-3 py-1 rounded ${
                activeTab === 'knowledge' ? 'bg-blue-500 text-white' : 'bg-gray-200'
              }`}
            >
              知识库
            </button>
          </nav>
        </div>
        {activeTab === 'chat' ? <SessionList /> : <KnowledgePanel />}
      </div>
      <div className="flex-1">
        <ChatView />
      </div>
    </div>
  );
}

export default App;
```

**Step 7: 提交**

```bash
cd frontend
git add src/api/client.ts src/stores/knowledgeStore.ts src/components/knowledge/
git commit -m "feat: add knowledge base management UI"
```

---

## Phase 4: 实现会话摘要功能

### Task 6: 添加会话摘要生成服务

**Files:**
- Create: `backend/app/services/summary_service.py`
- Modify: `backend/app/services/session_service.py`
- Test: `backend/tests/test_summary_service.py`

**Step 1: 编写失败的测试**

```python
# tests/test_summary_service.py
import pytest
from app.services.summary_service import get_summary_service


@pytest.mark.asyncio
async def test_generate_summary():
    """Test generating a session summary"""
    service = get_summary_service()

    messages = [
        {"role": "user", "content": "你好，我想咨询关于合同的问题"},
        {"role": "assistant", "content": "你好！我可以帮您解答合同相关的法律问题..."},
        {"role": "user", "content": "合同违约后如何赔偿？"},
        {"role": "assistant", "content": "根据《民法典》规定..."}
    ]

    summary = await service.generate_summary(messages)

    assert summary is not None
    assert len(summary) > 0
    assert "合同" in summary
```

**Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_summary_service.py::test_generate_summary -v
```

Expected: FAIL with module not found

**Step 3: 实现摘要服务**

```python
# app/services/summary_service.py
from typing import List, Dict, Any
from app.services.llm_service import get_llm_service
import logging

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """你是一个专业的对话总结助手。请将以下对话内容总结为简洁的标题（不超过20字）。
标题应该反映对话的主要主题，比如"合同违约咨询"、"劳动纠纷问题"等。只返回标题，不要有其他内容。"""


class SummaryService:
    """Service for generating conversation summaries"""

    def __init__(self):
        self.llm_service = get_llm_service()

    async def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a summary title for a conversation

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            A concise title for the conversation
        """
        if not messages:
            return "新对话"

        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages[-6:]  # Use last 6 messages
            ])

            prompt = f"请为以下对话生成一个简洁标题：\n\n{conversation_text}"

            # Use empty history since we just want a summary
            summary = await self.llm_service.generate_response(
                message=prompt,
                conversation_history=[],
                system_prompt=SUMMARY_SYSTEM_PROMPT
            )

            # Clean up the response
            summary = summary.strip().strip('\'"').strip('【】').strip('《》')

            # Limit length
            if len(summary) > 30:
                summary = summary[:27] + "..."

            logger.info(f"Generated summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback to first user message snippet
            user_messages = [m for m in messages if m["role"] == "user"]
            if user_messages:
                first_msg = user_messages[0]["content"]
                return first_msg[:20] + ("..." if len(first_msg) > 20 else "")
            return "对话"


# Singleton
_summary_service = None


def get_summary_service() -> SummaryService:
    """Get or create the summary service"""
    global _summary_service
    if _summary_service is None:
        _summary_service = SummaryService()
    return _summary_service
```

**Step 4: 更新 SessionService 集成摘要**

```python
# app/services/session_service.py (add method)
from app.services.summary_service import get_summary_service


async def generate_and_update_summary(self, session_id: str) -> str:
    """Generate a summary for a session and update it"""
    message_service = MessageService(self.db)
    messages = await message_service.get_messages_by_session(session_id)

    if len(messages) < 2:
        return None  # Don't summarize conversations with less than 2 messages

    # Convert to format expected by summary service
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    # Generate summary
    summary_service = get_summary_service()
    summary = await summary_service.generate_summary(conversation_history)

    # Update session
    await self.update_session(session_id, SessionUpdate(title=summary))

    return summary
```

**Step 5: 运行测试验证通过**

```bash
cd backend
pytest tests/test_summary_service.py::test_generate_summary -v
```

Expected: PASS

**Step 6: 提交**

```bash
cd backend
git add app/services/summary_service.py app/services/session_service.py tests/test_summary_service.py
git commit -m "feat: add conversation summary service"
```

---

### Task 7: 在聊天端点自动生成摘要

**Files:**
- Modify: `backend/app/api/v1/chat.py`

**Step 1: 修改聊天端点添加自动摘要**

```python
# app/api/v1/chat.py (modify existing chat endpoint)

@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Send a message and get a response from the agent system"""
    session_service = SessionService(db)
    message_service = MessageService(db)
    agent_graph = get_agent_graph()

    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = request.session_id
        messages = await message_service.get_messages_by_session(session_id)
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-10:]
        ]
    else:
        new_session = await session_service.create_session({"title": None})
        session_id = new_session.id
        conversation_history = []

    try:
        # Prepare state for agent
        state = create_initial_state(str(session_id), request.message, conversation_history)

        # Run the agent graph
        final_state = await agent_graph.invoke(state)

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
                "model": "qwen-via-langgraph",
                "sources": sources,
                "intent": final_state.get("user_intent", "unknown")
            }
        )

        # Update session message count
        await session_service.increment_message_count(session_id)

        # Auto-generate summary if this is a new session or has no title
        session = await session_service.get_session(session_id)
        if not session.title or session.title == "新对话":
            await session_service.generate_and_update_summary(session_id)
            # Refresh to get the updated title
            session = await session_service.get_session(session_id)

        return {
            "session_id": session_id,
            "response": response_content,
            "sources": sources,
            "title": session.title  # Include the generated title
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")
```

**Step 2: 提交**

```bash
cd backend
git add app/api/v1/chat.py
git commit -m "feat: auto-generate session summary on first message"
```

---

## Phase 5: 完善前端样式和用户体验

### Task 8: 添加前端样式优化

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/chat/ChatView.tsx`
- Create: `frontend/src/index.css`

**Step 1: 添加全局样式**

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
```

**Step 2: 更新 main.tsx 引入样式**

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**Step 3: 添加 Tailwind CSS 配置**

```bash
cd frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Step 4: 配置 Tailwind**

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Step 5: 提交**

```bash
cd frontend
git add src/index.css src/main.tsx tailwind.config.js postcss.config.js package.json package-lock.json
git commit -m "style: add Tailwind CSS and global styles"
```

---

## Phase 6: 完善测试覆盖

### Task 9: 添加端到端测试

**Files:**
- Create: `backend/tests/test_e2e_full_flow.py`

**Step 1: 编写完整的 E2E 测试**

```python
# tests/test_e2e_full_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
import tempfile
import os

client = TestClient(app)


def test_full_knowledge_to_chat_flow():
    """Test the complete flow from uploading a document to querying it"""

    # 1. Upload a legal document
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("民法典第五百七十七条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。")
        temp_path = f.name

    try:
        with open(temp_path, 'rb') as f:
            upload_response = client.post(
                "/api/v1/knowledge/upload",
                files={"file": ("合同法.txt", f, "text/plain")},
                data={"title": "合同违约责任", "category": "law"}
            )

        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        # 2. Verify document is in the list
        list_response = client.get("/api/v1/knowledge/documents")
        assert list_response.status_code == 200
        documents = list_response.json()["documents"]
        assert any(d["id"] == document_id for d in documents)

        # 3. Ask a legal question that should use the uploaded document
        chat_response = client.post("/api/v1/chat", json={
            "message": "合同违约需要承担什么责任？"
        })

        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "response" in chat_data
        assert "违约责任" in chat_data["response"] or "继续履行" in chat_data["response"]

        # 4. Clean up - delete the document
        delete_response = client.delete(f"/api/v1/knowledge/documents/{document_id}")
        assert delete_response.status_code == 200

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_multi_turn_conversation():
    """Test a multi-turn conversation with context"""

    # First message
    response1 = client.post("/api/v1/chat", json={
        "message": "你好，我想咨询法律问题"
    })
    assert response1.status_code == 200
    session_id = response1.json()["session_id"]

    # Second message with context
    response2 = client.post("/api/v1/chat", json={
        "session_id": session_id,
        "message": "请问合同违约怎么赔偿？"
    })
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["session_id"] == session_id
    assert len(data2["response"]) > 0

    # Verify session was created
    session_response = client.get(f"/api/v1/sessions/{session_id}")
    assert session_response.status_code == 200
    session_data = session_response.json()
    assert session_data["message_count"] >= 2


def test_session_listing_and_deletion():
    """Test session management"""

    # Create multiple sessions
    session_ids = []
    for i in range(3):
        response = client.post("/api/v1/chat", json={
            "message": f"测试消息 {i+1}"
        })
        session_ids.append(response.json()["session_id"])

    # List sessions
    list_response = client.get("/api/v1/sessions")
    assert list_response.status_code == 200
    sessions = list_response.json()
    assert len(sessions) >= 3

    # Delete a session
    delete_response = client.delete(f"/api/v1/sessions/{session_ids[0]}")
    assert delete_response.status_code == 200

    # Verify deletion
    list_response2 = client.get("/api/v1/sessions")
    sessions2 = list_response2.json()
    assert not any(s["id"] == session_ids[0] for s in sessions2)
```

**Step 2: 运行 E2E 测试**

```bash
cd backend
pytest tests/test_e2e_full_flow.py -v
```

Expected: All tests PASS

**Step 3: 提交**

```bash
cd backend
git add tests/test_e2e_full_flow.py
git commit -m "test: add comprehensive end-to-end tests"
```

---

## Phase 7: 文档和部署准备

### Task 10: 完善项目文档

**Files:**
- Modify: `README.md`
- Create: `backend/DEPLOYMENT.md`
- Create: `frontend/DEPLOYMENT.md`

**Step 1: 更新主 README**

```markdown
# 法律咨询助手 (Legal Consultation Assistant)

基于阿里云 DashScope Qwen 和 LangChain/LangGraph 的 AI 法律咨询平台。

## 功能特性

- 多轮法律咨询对话
- 上下文感知的对话管理
- 基于 RAG 的知识库检索（ChromaDB + DashScope Embeddings）
- 会话管理和自动摘要
- LangChain/LangGraph Agent 编排
- 管理员知识库管理界面
- 流式响应支持

## 技术栈

- **后端:** FastAPI, Python, LangChain, LangGraph
- **LLM:** 阿里云 DashScope Qwen (qwen-plus)
- **Embeddings:** DashScope text-embedding-v3
- **前端:** React, TypeScript, Vite, TailwindCSS
- **数据库:** SQLite (本地), PostgreSQL (生产)
- **向量数据库:** ChromaDB
- **Agent 框架:** LangChain + LangGraph

## 快速开始

### 后端

1. 配置环境变量:
```bash
cd backend
cp .env.example .env
# 编辑 .env 填入你的 DashScope API Key
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 初始化数据库:
```bash
python create_tables.py
```

4. 启动服务:
```bash
uvicorn app.main:app --reload
```

### 前端

1. 安装依赖:
```bash
cd frontend
npm install
```

2. 启动开发服务器:
```bash
npm run dev
```

3. 打开 http://localhost:5173

## 环境变量

参见 `.env.example` 获取所需变量:

- `DASHSCOPE_API_KEY`: 阿里云 DashScope API 密钥（必需）
- `DASHSCOPE_MODEL`: 使用的 Qwen 模型（默认: qwen-plus）
- `DASHSCOPE_EMBEDDING_MODEL`: Embedding 模型（默认: text-embedding-v3）

获取 API Key: https://dashscope.console.aliyun.com/

## API 文档

启动后端后访问 http://localhost:8000/docs

## 测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端测试
cd frontend
npm test
```

## 架构

系统使用 LangGraph 编排多个 Agent:

1. **Intent Router Agent**: 分类用户意图（问候、法律咨询、普通聊天）
2. **RAG Retriever Agent**: 使用 DashScope embeddings 搜索知识库
3. **Response Generator Agent**: 使用 Qwen 结合检索上下文生成回复

## Agent 流程

```
用户输入 → Intent Router → RAG Retriever → Response Generator → 输出
                                ↓
                          (periodically)
                    Summary Generator Agent
```

## License

MIT
```

**Step 2: 创建后端部署文档**

```markdown
# Backend Deployment Guide

## Development Setup

1. Install Python 3.7+
2. Create virtual environment: `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/legal_consultation.db
DATABASE_URL_SYNC=sqlite:///./data/legal_consultation.db

# DashScope
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3

# ChromaDB
CHROMA_DB_PATH=./data/chroma
CHROMA_COLLECTION_NAME=legal_knowledge

# App
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

## Database Setup

```bash
python create_tables.py
```

## Running

Development:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Production Considerations

1. Use PostgreSQL instead of SQLite
2. Set up proper logging
3. Enable CORS for production domains
4. Use environment variable management (e.g., AWS Secrets Manager)
5. Set up monitoring (e.g., Sentry)
```

**Step 3: 创建前端部署文档**

```markdown
# Frontend Deployment Guide

## Development Setup

1. Install Node.js 18+
2. Install dependencies: `npm install`
3. Start dev server: `npm run dev`

## Environment Variables

Create `.env` file:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

## Building

```bash
npm run build
```

Output will be in `dist/` directory.

## Deployment

### Vercel

1. Connect repository
2. Set environment variable: `VITE_API_URL`
3. Deploy

### Netlify

1. Connect repository
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Set environment variable: `VITE_API_URL`

### Docker

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

## Production Considerations

1. Enable proper error tracking (Sentry)
2. Add analytics
3. Optimize bundle size
4. Enable HTTPS
5. Configure proper CORS
```

**Step 4: 提交**

```bash
git add README.md backend/DEPLOYMENT.md frontend/DEPLOYMENT.md
git commit -m "docs: add comprehensive deployment documentation"
```

---

## 总结

此实施计划包含 10 个主要任务，覆盖以下功能：

1. ✅ 知识库文档列表 API
2. ✅ 文档上传 API
3. ✅ 文档删除 API
4. ✅ 流式聊天响应
5. ✅ 前端知识库管理界面
6. ✅ 会话摘要生成服务
7. ✅ 自动摘要触发
8. ✅ 前端样式优化
9. ✅ 端到端测试
10. ✅ 部署文档

每个任务都遵循 TDD 方法论，包含完整的测试、实现和提交步骤。
