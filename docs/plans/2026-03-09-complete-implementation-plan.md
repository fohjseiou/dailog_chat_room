# 法律咨询助手平台 - 完整实施计划

> **创建日期:** 2026-03-09
> **Python 版本:** 3.11.6 (D:\softwore\python3.11.6\libs)
> **当前分支:** master (feature/implementation 可用于开发)

## 项目概述

**目标:** 完成基于阿里云 DashScope Qwen + LangChain/LangGraph 的 AI 法律咨询平台

**核心功能:**
- 多轮法律咨询对话
- RAG 知识库检索
- 会话管理与自动摘要
- 知识库管理面板

**技术架构:**
```
Frontend (React + TypeScript + Vite)
    ↓
Backend (FastAPI + Python 3.11.6)
    ↓
LangGraph Agent System (Intent Router → RAG Retriever → Response Generator)
    ↓                    ↓
DashScope Qwen LLM   ChromaDB + DashScope Embeddings
```

---

## 当前实现状态

### ✅ 已完成

**后端:**
- FastAPI 项目结构和配置
- 数据库模型 (Session, Message, KnowledgeDocument)
- Pydantic schemas
- Session 和 Message CRUD 服务
- LLM 服务 (DashScope Qwen)
- Embedding 服务 (text-embedding-v3)
- ChromaDB 向量存储服务
- 文档处理服务 (PDF/DOCX/TXT)
- 文本分块服务
- LangGraph agent 结构 (Intent Router, RAG Retriever, Response Generator)
- 聊天 API 端点 (`/api/v1/chat`)
- Session API 端点 (`/api/v1/sessions`)
- 测试框架

**前端:**
- React + TypeScript + Vite 项目
- ChatView 组件
- SessionList 组件
- MessageBubble 组件
- MessageInput 组件
- API client (axios)
- Zustand 状态管理

### 🔄 需要完善

**后端:**
- 知识库管理 API (当前是占位符)
- 流式响应支持
- 会话摘要生成功能

**前端:**
- 知识库管理界面
- 流式聊天显示
- 会话详情页
- 样式优化

### ⏳ 待实现

- 知识库文档 CRUD 完整实现
- 文档上传处理
- 流式聊天响应 SSE/Streaming
- 会话自动摘要
- 前端路由和页面组织
- UI/UX 优化

---

## 实施计划

### Phase 1: 后端知识库管理 API (优先级: 高)

#### Task 1.1: 实现知识库文档列表 API

**文件:** `backend/app/api/v1/knowledge.py`

**实现内容:**
```python
# GET /api/v1/knowledge/documents - 获取文档列表
# 查询参数: page, page_size, search
# 返回: { documents: [...], total: number, page: number, page_size: number }
```

#### Task 1.2: 实现文档上传 API

**文件:** `backend/app/api/v1/knowledge.py`

**实现内容:**
```python
# POST /api/v1/knowledge/documents/upload - 上传文档
# 接受: multipart/form-data (file, title, category)
# 处理: PDF/DOCX/TXT 解析 → 分块 → Embedding → 存储到 ChromaDB + SQLite
# 返回: { document_id, title, chunk_count, status }
```

#### Task 1.3: 实现文档详情 API

**文件:** `backend/app/api/v1/knowledge.py`

**实现内容:**
```python
# GET /api/v1/knowledge/documents/{id} - 获取文档详情
# DELETE /api/v1/knowledge/documents/{id} - 删除文档
# PUT /api/v1/knowledge/documents/{id} - 更新文档元数据
```

#### Task 1.4: 实现知识库统计 API

**文件:** `backend/app/api/v1/knowledge.py`

**实现内容:**
```python
# GET /api/v1/knowledge/stats - 获取统计信息
# 返回: { total_documents, total_chunks, categories, storage_size }
```

**测试文件:** `backend/tests/test_knowledge_api.py`

---

### Phase 2: 后端流式响应支持 (优先级: 高)

#### Task 2.1: 实现 SSE 流式响应端点

**文件:** `backend/app/api/v1/chat.py`

**实现内容:**
```python
# POST /api/v1/chat/stream - 流式聊天
# 使用 Server-Sent Events (SSE)
# 逐步返回: intent → retrieved_docs → response_chunks
```

#### Task 2.2: 更新 LLM 服务支持流式输出

**文件:** `backend/app/services/llm_service.py`

**实现内容:**
```python
async def generate_stream(messages: List[Dict]) -> AsyncIterator[str]:
    """使用 DashScope SDK 的流式 API"""
```

#### Task 2.3: 更新 Agent Graph 支持流式

**文件:** `backend/app/agents/graph.py`, `backend/app/agents/nodes.py`

**实现内容:**
- 修改 response_generator_node 支持流式输出
- 使用 `astream_events` 逐步返回状态

**测试文件:** `backend/tests/test_streaming.py`

---

### Phase 3: 后端会话摘要功能 (优先级: 中)

#### Task 3.1: 实现摘要生成服务

**文件:** `backend/app/services/summary_service.py`

**实现内容:**
```python
class SummaryService:
    async def generate_summary(session_id: str) -> str:
        """当消息数达到阈值时自动生成摘要"""
```

#### Task 3.2: 集成到聊天流程

**文件:** `backend/app/api/v1/chat.py`

**实现内容:**
- 在消息保存后检查是否需要生成摘要
- 触发异步摘要生成任务

#### Task 3.3: 实现摘要查询 API

**文件:** `backend/app/api/v1/sessions.py`

**实现内容:**
```python
# GET /api/v1/sessions/{id}/summary - 获取会话摘要
```

---

### Phase 4: 前端知识库管理界面 (优先级: 高)

#### Task 4.1: 创建知识库页面结构

**文件:**
- `frontend/src/pages/KnowledgePage.tsx`
- `frontend/src/components/knowledge/KnowledgeList.tsx`
- `frontend/src/components/knowledge/DocumentUploader.tsx`
- `frontend/src/components/knowledge/DocumentCard.tsx`

#### Task 4.2: 实现文档列表功能

**实现内容:**
- 显示文档列表 (分页)
- 搜索和过滤
- 分类标签

#### Task 4.3: 实现文档上传功能

**实现内容:**
- 拖拽上传
- 文件类型验证
- 上传进度显示
- 上传成功/失败提示

#### Task 4.4: 实现文档操作功能

**实现内容:**
- 查看文档详情
- 删除文档
- 编辑元数据

#### Task 4.5: 添加知识库统计面板

**实现内容:**
- 文档数量统计
- 存储空间统计
- 分类分布图表

---

### Phase 5: 前端流式聊天显示 (优先级: 高)

#### Task 5.1: 实现 SSE 客户端

**文件:** `frontend/src/api/streamingClient.ts`

**实现内容:**
```typescript
export async function* streamChat(request: ChatRequest): AsyncGenerator<StreamChunk>
```

#### Task 5.2: 更新 ChatStore 支持流式

**文件:** `frontend/src/stores/chatStore.ts`

**实现内容:**
- 添加流式消息状态管理
- 实时更新消息内容

#### Task 5.3: 更新 MessageBubble 组件

**文件:** `frontend/src/components/chat/MessageBubble.tsx`

**实现内容:**
- 显示流式输入动画
- 显示检索到的文档来源
- Markdown 渲染支持

#### Task 5.4: 添加思考状态显示

**实现内容:**
- 显示 Agent 当前状态 (路由中/检索中/生成中)
- 显示检索到的相关文档片段

---

### Phase 6: 前端路由和页面组织 (优先级: 中)

#### Task 6.1: 设置 React Router

**文件:** `frontend/src/App.tsx`, `frontend/src/main.tsx`

**实现内容:**
```typescript
// 路由结构:
/ - 聊天页面 (主页)
/knowledge - 知识库管理页面
/sessions/:id - 会话详情页
/settings - 设置页面
```

#### Task 6.2: 创建导航组件

**文件:** `frontend/src/components/layout/Navigation.tsx`

**实现内容:**
- 顶部导航栏
- 侧边栏 (移动端)

#### Task 6.3: 实现会话详情页

**文件:** `frontend/src/pages/SessionDetailPage.tsx`

**实现内容:**
- 显示会话完整历史
- 显示会话摘要
- 导出对话功能

---

### Phase 7: UI/UX 优化 (优先级: 中)

#### Task 7.1: 添加 Tailwind CSS

**实现内容:**
- 安装 Tailwind CSS
- 配置主题
- 添加常用组件样式

#### Task 7.2: 优化聊天界面

**实现内容:**
- 改进消息气泡样式
- 添加代码高亮
- 添加 Markdown 渲染
- 添加复制按钮

#### Task 7.3: 添加加载和错误状态

**实现内容:**
- 骨架屏
- 友好的错误提示
- 重试机制

#### Task 7.4: 响应式设计

**实现内容:**
- 移动端适配
- 平板适配
- 触摸操作优化

---

### Phase 8: 测试和文档 (优先级: 中)

#### Task 8.1: 后端测试

**实现内容:**
- 知识库 API 测试
- 流式响应测试
- 摘要功能测试
- 集成测试

#### Task 8.2: 前端测试

**实现内容:**
- 组件单元测试
- 集成测试
- E2E 测试

#### Task 8.3: API 文档

**实现内容:**
- 更新 OpenAPI 文档
- 添加使用示例
- 添加错误码说明

#### Task 8.4: 部署文档

**实现内容:**
- 环境配置指南
- 部署步骤
- 故障排查

---

## 环境配置

### 后端环境变量 (.env)

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/legal.db
DATABASE_URL_SYNC=sqlite:///./data/legal.db

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

# Summary
SUMMARY_MESSAGE_THRESHOLD=10
SUMMARY_TOKEN_THRESHOLD=8000
```

### 前端环境变量 (.env)

```bash
VITE_API_URL=http://127.0.0.1:8000
```

---

## 开发工作流

### 启动开发环境

```bash
# 后端
cd backend
# 确保使用 Python 3.11.6
D:\softwore\python3.11.6\python.exe -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python create_tables.py
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### Git 工作流

```bash
# 创建功能分支
git checkout -b feature/implementation

# 开发并提交
git add .
git commit -m "feat: xxx"

# 推送到远程
git push origin feature/implementation

# 完成后合并到 master
git checkout master
git merge feature/implementation
```

---

## 依赖清单

### 后端主要依赖

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
aiosqlite==0.19.0
alembic==1.13.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
dashscope==1.14.1
langchain==0.1.0
langgraph==0.0.2
chromadb==0.4.18
pypdf==3.17.0
python-docx==1.1.0
structlog==23.2.0
```

### 前端主要依赖

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.13.6",
    "lucide-react": "^0.577.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "zustand": "^4.5.7"
  }
}
```

---

## 预计工作量

| Phase | 描述 | 预计时间 |
|-------|------|---------|
| 1 | 后端知识库管理 API | 1-2 天 |
| 2 | 后端流式响应支持 | 1 天 |
| 3 | 后端会话摘要功能 | 0.5 天 |
| 4 | 前端知识库管理界面 | 1-2 天 |
| 5 | 前端流式聊天显示 | 1 天 |
| 6 | 前端路由和页面组织 | 0.5 天 |
| 7 | UI/UX 优化 | 1 天 |
| 8 | 测试和文档 | 1 天 |

**总计:** 约 7-9 天

---

## 下一步行动

1. 确认 Python 环境配置正确 (3.11.6)
2. 确认 DashScope API key 可用
3. 从 Phase 1 Task 1.1 开始实施
4. 每完成一个 Phase 进行测试验证
5. 定期提交代码到 feature/implementation 分支

---

**备注:** 本计划基于当前代码库状态分析生成，实施过程中可能需要根据实际情况调整。建议按 Phase 顺序逐步实施，每个 Phase 完成后进行测试验证再进入下一阶段。
