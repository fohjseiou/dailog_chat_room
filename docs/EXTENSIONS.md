# 扩展点文档

本文档详细列出了当前系统 (v0.2.0) 中可扩展的接口和扩展点，方便开发者进行功能扩展和定制。

---

## 目录

- [后端扩展点](#后端扩展点)
- [前端扩展点](#前端扩展点)
- [Agent 扩展点](#agent-扩展点)
- [存储扩展点](#存储扩展点)
- [集成扩展点](#集成扩展点)

---

## 后端扩展点

### 1. Agent 节点扩展

**位置**: `backend/app/agents/nodes.py`

**当前节点**:
- `intent_classifier_node` - 意图分类
- `legal_consultation_node` - 法律咨询
- `greeting_node` - 问候响应
- `general_chat_node` - 一般对话
- `response_generator_node` - 响应生成
- `response_generator_node_stream` - 流式响应生成

**扩展示例**:

```python
# 添加新的意图类型节点
async def contract_review_node(state: AgentState) -> AgentState:
    """合同审查专用节点"""
    # 实现合同审查逻辑
    state.response = "合同审查结果..."
    state.intent = "contract_review"
    return state

# 在 graph.py 中注册新节点
def create_agent_graph():
    graph = StateGraph(AgentState)
    # ... 现有节点
    graph.add_node("contract_review", contract_review_node)

    # 添加新的条件边
    graph.add_conditional_edges(
        "intent_classifier",
        should_route,
        {
            "contract_review": "contract_review",
            # ... 其他路由
        }
    )
    return graph.compile()
```

### 2. API 路由扩展

**位置**: `backend/app/api/v1/`

**当前路由**:
- `/api/v1/chat` - 聊天接口
- `/api/v1/sessions` - 会话管理
- `/api/v1/knowledge` - 知识库管理

**扩展示例**:

```python
# app/api/v1/export.py
from fastapi import APIRouter, HTTPException
from app.schemas.export import ExportRequest, ExportResponse

router = APIRouter(prefix="/export", tags=["export"])

@router.post("/conversation", response_model=ExportResponse)
async def export_conversation(request: ExportRequest):
    """导出对话"""
    # 实现导出逻辑
    pass

@router.post("/knowledge", response_model=ExportResponse)
async def export_knowledge(request: ExportRequest):
    """导出知识库"""
    # 实现导出逻辑
    pass

# 在 app/api/v1/__init__.py 中注册
from app.api.v1 import export
api_router.include_router(export.router)
```

### 3. Service 层扩展

**位置**: `backend/app/services/`

**当前服务**:
- `message_service.py` - 消息服务
- `session_service.py` - 会话服务
- `knowledge_service.py` - 知识库服务
- `summary_service.py` - 摘要服务

**扩展示例**:

```python
# app/services/export_service.py
from typing import Dict, Any, Optional
from app.services.session_service import SessionService

class ExportService:
    """导出服务"""

    def __init__(self):
        self.session_service = SessionService()

    async def export_session_to_txt(
        self,
        session_id: str,
        include_metadata: bool = True
    ) -> str:
        """导出会话为 TXT 格式"""
        # 实现导出逻辑
        pass

    async def export_session_to_markdown(
        self,
        session_id: str
    ) -> str:
        """导出会话为 Markdown 格式"""
        # 实现导出逻辑
        pass

    async def export_session_to_json(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """导出会话为 JSON 格式"""
        # 实现导出逻辑
        pass
```

### 4. 数据库 Model 扩展

**位置**: `backend/app/models/`

**当前模型**:
- `session.py` - 会话模型
- `message.py` - 消息模型
- `knowledge.py` - 知识库模型

**扩展示例**:

```python
# app/models/user.py
from sqlalchemy import Column, String, DateTime, Boolean
from app.database import Base
from datetime import datetime

class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# app/models/favorite.py
class Favorite(Base):
    """收藏模型"""
    __tablename__ = "favorites"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 5. Schema 扩展

**位置**: `backend/app/schemas/`

**当前 Schema**:
- `session.py` - 会话 Schema
- `message.py` - 消息 Schema
- `knowledge.py` - 知识库 Schema

**扩展示例**:

```python
# app/schemas/export.py
from pydantic import BaseModel
from enum import Enum

class ExportFormat(str, Enum):
    """导出格式"""
    TXT = "txt"
    MARKDOWN = "md"
    JSON = "json"
    PDF = "pdf"

class ExportRequest(BaseModel):
    """导出请求"""
    session_id: str
    format: ExportFormat
    include_metadata: bool = True
    include_sources: bool = True

class ExportResponse(BaseModel):
    """导出响应"""
    download_url: str
    filename: str
    size_bytes: int
    created_at: str
```

### 6. 中间件扩展

**位置**: `backend/app/main.py`

**当前中间件**:
- CORS 中间件
- 异常处理中间件

**扩展示例**:

```python
# app/middleware/logging.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        logger.info(f"{request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Status: {response.status_code}")
        return response

# app/middleware/rate_limit.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.request_history = {}

    async def dispatch(self, request: Request, call_next):
        # 实现速率限制逻辑
        pass
```

---

## 前端扩展点

### 1. Store 扩展

**位置**: `frontend/src/stores/`

**当前 Store**:
- `chatStore.ts` - 聊天状态
- `knowledgeStore.ts` - 知识库状态
- `sessionStore.ts` - 会话状态

**扩展示例**:

```typescript
// src/stores/exportStore.ts
import { create } from 'zustand';

interface ExportState {
  // 状态
  exporting: boolean;
  exportHistory: ExportRecord[];

  // 操作
  exportSession: (sessionId: string, format: ExportFormat) => Promise<void>;
  getExportHistory: () => Promise<void>;
}

interface ExportRecord {
  id: string;
  sessionId: string;
  format: ExportFormat;
  filename: string;
  createdAt: string;
}

export const useExportStore = create<ExportState>((set, get) => ({
  exporting: false,
  exportHistory: [],

  exportSession: async (sessionId: string, format: ExportFormat) => {
    set({ exporting: true });
    try {
      const result = await exportApi.exportSession(sessionId, format);
      // 处理导出结果
    } finally {
      set({ exporting: false });
    }
  },

  getExportHistory: async () => {
    // 获取导出历史
  },
}));
```

### 2. API 客户端扩展

**位置**: `frontend/src/api/client.ts`

**当前 API**:
- `chatApi` - 聊天 API
- `sessionApi` - 会话 API
- `knowledgeApi` - 知识库 API

**扩展示例**:

```typescript
// src/api/client.ts 扩展
export const exportApi = {
  // 导出会话
  exportSession: async (sessionId: string, format: ExportFormat) => {
    const response = await api.post(`/api/v1/export/conversation`, {
      session_id: sessionId,
      format: format,
    });
    return response.data;
  },

  // 下载导出文件
  downloadExport: async (exportId: string) => {
    const response = await api.get(`/api/v1/export/download/${exportId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // 获取导出历史
  getExportHistory: async (params: PaginationParams) => {
    const response = await api.get(`/api/v1/export/history`, { params });
    return response.data;
  },
};
```

### 3. 组件扩展

**位置**: `frontend/src/components/`

**当前组件**:
- `chat/` - 聊天组件
- `knowledge/` - 知识库组件
- `sessions/` - 会话组件
- `layout/` - 布局组件
- `ui/` - UI 组件

**扩展示例**:

```typescript
// src/components/export/ExportButton.tsx
import { TouchButton } from '../ui/Button';
import { useExportStore } from '../../stores/exportStore';

interface ExportButtonProps {
  sessionId: string;
}

export function ExportButton({ sessionId }: ExportButtonProps) {
  const { exporting, exportSession } = useExportStore();

  const handleExport = async (format: ExportFormat) => {
    await exportSession(sessionId, format);
  };

  return (
    <div className="flex gap-2">
      <TouchButton
        size="sm"
        variant="ghost"
        onClick={() => handleExport(ExportFormat.TXT)}
        disabled={exporting}
      >
        导出 TXT
      </TouchButton>
      <TouchButton
        size="sm"
        variant="ghost"
        onClick={() => handleExport(ExportFormat.MARKDOWN)}
        disabled={exporting}
      >
        导出 MD
      </TouchButton>
      <TouchButton
        size="sm"
        variant="ghost"
        onClick={() => handleExport(ExportFormat.JSON)}
        disabled={exporting}
      >
        导出 JSON
      </TouchButton>
    </div>
  );
}
```

### 4. 路由扩展

**位置**: `frontend/src/App.tsx`

**当前路由**:
- `/` - 聊天页面
- `/knowledge` - 知识库页面
- `/sessions` - 会话列表
- `/sessions/:id` - 会话详情

**扩展示例**:

```typescript
// src/App.tsx 扩展
import { ExportHistoryPage } from './components/export/ExportHistoryPage';
import { SettingsPage } from './components/settings/SettingsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 现有路由 */}
        <Route path="/" element={<ChatView />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/sessions" element={<SessionsList />} />
        <Route path="/sessions/:id" element={<SessionDetailPage />} />

        {/* 新增路由 */}
        <Route path="/export" element={<ExportHistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
      <ToastContainer />
    </BrowserRouter>
  );
}
```

---

## Agent 扩展点

### 1. 意图分类扩展

**位置**: `backend/app/agents/nodes.py` - `intent_classifier_node`

**当前意图**:
- `greeting` - 问候
- `legal_consultation` - 法律咨询
- `general_chat` - 一般对话

**扩展示例**:

```python
# 添加新的意图类型
INTENT_CATEGORIES = {
    "greeting": "问候",
    "legal_consultation": "法律咨询",
    "general_chat": "一般对话",
    "contract_review": "合同审查",      # 新增
    "case_analysis": "案例分析",        # 新增
    "document_query": "文档查询",       # 新增
}

async def intent_classifier_node(state: AgentState) -> AgentState:
    """意图分类节点（扩展版）"""
    user_input = state.messages[-1]["content"]

    # 使用 LLM 进行意图分类
    prompt = f"""
    请分类以下用户输入的意图类型：

    {user_input}

    可能的意图类型：
    - greeting: 问候
    - legal_consultation: 法律咨询
    - general_chat: 一般对话
    - contract_review: 合同审查
    - case_analysis: 案例分析
    - document_query: 文档查询

    只返回意图类型（英文）。
    """

    response = await llm_service.generate(prompt)
    intent = response.strip().lower()

    # 验证意图有效性
    if intent not in INTENT_CATEGORIES:
        intent = "general_chat"

    state.intent = intent
    return state
```

### 2. 知识检索扩展

**位置**: `backend/app/agents/nodes.py` - `legal_consultation_node`

**当前检索**:
- ChromaDB 向量检索
- 固定 top_k = 3

**扩展示例**:

```python
# 增强的检索节点
async def enhanced_retrieval_node(state: AgentState) -> AgentState:
    """增强的检索节点"""

    query = state.messages[-1]["content"]
    intent = state.intent

    # 根据意图类型调整检索策略
    retrieval_params = {
        "legal_consultation": {"top_k": 5, "min_score": 0.6},
        "contract_review": {"top_k": 10, "min_score": 0.7},
        "case_analysis": {"top_k": 8, "min_score": 0.65},
        "document_query": {"top_k": 3, "min_score": 0.5},
    }

    params = retrieval_params.get(intent, {"top_k": 3, "min_score": 0.6})

    # 多策略检索
    results = []

    # 1. 向量检索
    vector_results = await chroma_service.query(
        query_text=query,
        n_results=params["top_k"]
    )

    # 2. 关键词检索（用于合同审查）
    if intent == "contract_review":
        keyword_results = await keyword_search_service.search(query)
        results.extend(keyword_results)

    # 3. 合并和去重
    results = merge_and_dedupe(vector_results, results)

    # 4. 过滤低分结果
    results = [r for r in results if r.score >= params["min_score"]]

    state.context = results[:params["top_k"]]
    state.retrieved_docs = [
        {"title": r.metadata.get("title", ""), "score": r.score}
        for r in results
    ]

    return state
```

---

## 存储扩展点

### 1. 向量存储扩展

**位置**: `backend/app/services/chroma_service.py`

**当前实现**: ChromaDB 本地存储

**扩展方向**:

```python
# 支持多种向量存储
class VectorStoreService(ABC):
    """向量存储抽象基类"""

    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> None:
        pass

    @abstractmethod
    async def query(self, query_text: str, n_results: int) -> List[QueryResult]:
        pass

class ChromaDBService(VectorStoreService):
    """ChromaDB 实现"""

class PineconeService(VectorStoreService):
    """Pinecone 实现"""

class WeaviateService(VectorStoreService):
    """Weaviate 实现"""

# 配置驱动的服务选择
def get_vector_store_service() -> VectorStoreService:
    provider = os.getenv("VECTOR_STORE_PROVIDER", "chroma")

    services = {
        "chroma": ChromaDBService,
        "pinecone": PineconeService,
        "weaviate": WeaviateService,
    }

    return services[provider]()
```

### 2. LLM 提供商扩展

**位置**: `backend/app/services/llm_service.py`

**当前实现**: DashScope Qwen

**扩展方向**:

```python
# 支持多种 LLM 提供商
class LLMService(ABC):
    """LLM 服务抽象基类"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        pass

class DashScopeLLMService(LLMService):
    """DashScope Qwen 实现"""

class OpenAILLMService(LLMService):
    """OpenAI GPT 实现"""

class AnthropicLLMService(LLMService):
    """Anthropic Claude 实现"""

class LocalLLMService(LLMService):
    """本地 LLM 实现 (Ollama)"""

# 配置驱动的服务选择
def get_llm_service() -> LLMService:
    provider = os.getenv("LLM_PROVIDER", "dashscope")

    services = {
        "dashscope": DashScopeLLMService,
        "openai": OpenAILLMService,
        "anthropic": AnthropicLLMService,
        "local": LocalLLMService,
    }

    return services[provider]()
```

---

## 集成扩展点

### 1. 认证集成

```python
# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """用户注册"""
    pass

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    pass

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """用户登出"""
    pass

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户信息"""
    pass
```

### 2. 通知集成

```python
# app/services/notification_service.py
class NotificationService:
    """通知服务"""

    async def send_email(self, to: str, subject: str, body: str):
        """发送邮件通知"""
        pass

    async def send_sms(self, to: str, message: str):
        """发送短信通知"""
        pass

    async def send_webhook(self, url: str, data: Dict[str, Any]):
        """发送 Webhook 通知"""
        pass
```

### 3. 存储集成

```python
# app/services/storage_service.py
class StorageService(ABC):
    """存储服务抽象基类"""

    @abstractmethod
    async def upload_file(self, file: UploadFile, path: str) -> str:
        """上传文件，返回 URL"""
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> None:
        """删除文件"""
        pass

class LocalStorageService(StorageService):
    """本地存储实现"""

class S3StorageService(StorageService):
    """AWS S3 实现"""

class AliyunOSSStorageService(StorageService):
    """阿里云 OSS 实现"""
```

---

## 配置扩展点

### 环境变量扩展

**`.env.example`**:

```bash
# 现有配置
DATABASE_URL=sqlite+aiosqlite:///./data/legal.db
DASHSCOPE_API_KEY=your_api_key_here

# 新增配置选项

# 认证
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# 存储
STORAGE_PROVIDER=local  # local, s3, aliyun_oss
S3_BUCKET_NAME=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
ALIYUN_OSS_BUCKET_NAME=
ALIYUN_OSS_ACCESS_KEY_ID=
ALIYUN_OSS_ACCESS_KEY_SECRET=

# 向量存储
VECTOR_STORE_PROVIDER=chroma  # chroma, pinecone, weaviate
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=

# LLM
LLM_PROVIDER=dashscope  # dashscope, openai, anthropic, local
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LOCAL_LLM_BASE_URL=http://localhost:11434

# 通知
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMS_PROVIDER=  # 阿里云, 腾讯云

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# 缓存
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

---

## 插件系统

### 插件接口定义

```python
# app/plugins/base.py
from abc import ABC, abstractmethod

class Plugin(ABC):
    """插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass

    @abstractmethod
    async def on_install(self) -> None:
        """安装时调用"""
        pass

    @abstractmethod
    async def on_uninstall(self) -> None:
        """卸载时调用"""
        pass

    @abstractmethod
    async def on_enable(self) -> None:
        """启用时调用"""
        pass

    @abstractmethod
    async def on_disable(self) -> None:
        """禁用时调用"""
        pass

# 示例插件
class ExportPlugin(Plugin):
    """导出功能插件"""

    @property
    def name(self) -> str:
        return "export"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def on_install(self) -> None:
        # 创建导出表
        pass

    async def on_uninstall(self) -> None:
        # 清理导出数据
        pass

    async def on_enable(self) -> None:
        # 注册导出路由
        pass

    async def on_disable(self) -> None:
        # 移除导出路由
        pass

    # 插件功能
    async def export_session(self, session_id: str, format: str) -> str:
        """导出会话"""
        pass
```

---

*最后更新: 2026-03-09*
