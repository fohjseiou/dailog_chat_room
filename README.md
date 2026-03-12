# 法律咨询助手 (Legal Consultation Assistant)

> 基于 DashScope Qwen + LangGraph 的 AI 法律咨询平台

AI-powered legal consultation platform with RAG-based responses, streaming chat, knowledge base management, and case search capabilities.

## 功能特性

### 💬 智能对话
- **多轮对话**: 支持上下文理解的多轮法律咨询
- **流式响应**: SSE 实时流式输出，提供更流畅的交互体验
- **意图识别**: 自动识别用户意图（法律咨询/案例搜索/问候/一般对话）
- **RAG 检索**: 基于向量检索的法律知识库问答
- **思考状态**: 实时显示 AI 处理状态（理解/检索/生成）
- **记忆系统**: 长期记忆和短期记忆，个性化用户体验

### 🔍 案例搜索
- **智能搜索**: 基于 Firecrawl 的法律案例网络搜索
- **自定义关键词**: 用户可输入具体的搜索关键词
- **相关案例推荐**: AI 回复后自动显示案例搜索按钮

### 👤 用户系统
- **用户注册/登录**: JWT 认证的安全用户系统
- **个性化记忆**: 基于用户历史对话的长期记忆提取
- **会话管理**: 完整的对话历史记录和会话切换
- **自动摘要**: AI 自动生成会话摘要

### 📚 知识库管理
- **文档上传**: 支持 PDF、DOCX、TXT 格式
- **智能分块**: 自动文档分块和向量化
- **分类管理**: 法律法规、案例分析、合同范本、司法解释
- **批量操作**: 文档列表、搜索、筛选、删除
- **统计面板**: 文档数量、知识块统计、分类分布

### 📱 响应式设计
- **移动端适配**: 完美的移动端体验
- **触摸优化**: 针对触摸交互的优化
- **侧边栏抽屉**: 移动端友好的导航

## 系统架构

### 架构流程图

```mermaid
graph TB
    subgraph "前端 Frontend"
        A[用户输入] --> B[MessageInput 组件]
        B --> C[chatStore 状态管理]
        C --> D[API 客户端]
    end

    subgraph "后端 Backend"
        D --> E[FastAPI 路由层]
        E --> F{意图路由}
        F -->|法律咨询| G[RAG 检索节点]
        F -->|案例搜索| H[案例搜索节点]
        F -->|其他| I[响应生成节点]

        G --> J[ChromaDB 向量检索]
        J --> K[上下文增强]
        K --> I

        H --> L[Firecrawl 网络搜索]
        L --> I

        I --> M[DashScope Qwen LLM]
        M --> N[响应输出]
    end

    subgraph "数据存储"
        O[(PostgreSQL)]
        P[(ChromaDB)]
    end

    E --> O
    G --> P

    N --> D
    D --> Q[消息显示]

    style A fill:#e1f5ff
    style M fill:#fff4e6
    style O fill:#f0f0f0
    style P fill:#f0f0f0
```

### Agent 节点流程

```mermaid
graph LR
    A[START] --> B[intent_router]
    B --> C{用户意图}

    C -->|legal_consultation| D[rag_retriever]
    C -->|case_search| E[case_search_node]
    C -->|其他| F[response_generator]

    D --> G[ChromaDB 检索]
    G --> F

    E --> H[Firecrawl 搜索]
    H --> F

    F --> I{用户已认证?}
    I -->|是| J[memory_extraction]
    I -->|否| K[END]
    J --> K

    style B fill:#e1f5ff
    style D fill:#fff4e6
    style E fill:#f0f9ff
    style F fill:#e8f5e9
    style J fill:#fce4ec
```

### 用户认证流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant A as API
    participant DB as 数据库

    U->>F: 输入用户名/密码
    F->>A: POST /api/v1/auth/login
    A->>DB: 验证用户凭证
    DB-->>A: 返回用户信息
    A-->>F: 返回 JWT Token
    F->>F: 存储 Token
    F->>U: 登录成功，跳转主页

    Note over F,DB: 后续请求自动携带 Token

    F->>A: GET /api/v1/chat (带 Token)
    A->>A: 验证 Token
    A->>DB: 处理请求
```

### 案例搜索流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant A as 后端
    participant L as LLM
    participant W as Firecrawl

    U->>F: 问法律问题
    F->>A: 发送消息
    A->>L: 获取回复

    Note over F: 显示"🔍 搜索相关案例"按钮

    U->>F: 点击搜索按钮
    F->>F: 弹出关键词输入框
    U->>F: 输入关键词（如"劳动合同纠纷"）
    F->>A: search_cases:劳动合同纠纷
    A->>A: 意图识别为 case_search
    A->>A: 调用 case_search_node
    A->>L: 使用工具调用搜索案例
    L->>W: Firecrawl API 调用
    W-->>L: 返回搜索结果
    L-->>A: 格式化的案例结果
    A-->>F: 返回案例列表
    F->>U: 显示案例搜索结果
```

## 技术架构

### 后端技术栈
- **框架**: FastAPI + Python 3.11+
- **LLM**: 阿里云 DashScope Qwen (qwen-plus/qwen-turbo)
- **Agent**: LangGraph (多节点编排)
- **向量存储**: ChromaDB + DashScope text-embedding-v3
- **数据库**: PostgreSQL
- **案例搜索**: Firecrawl (firecrawl-py)
- **异步**: asyncio + asyncpg
- **认证**: JWT + python-jose

### 前端技术栈
- **框架**: React 18 + TypeScript + Vite
- **状态管理**: Zustand
- **路由**: React Router v6
- **HTTP**: Axios
- **UI组件**: Ant Design + Lucide React
- **样式**: CSS Variables (类 Tailwind)

## 项目结构

```
dialog_chat_room/
├── backend/                        # 后端服务
│   ├── app/
│   │   ├── agents/                # LangGraph agents
│   │   │   ├── nodes.py           # Agent 节点定义
│   │   │   ├── graph.py           # 工作流编排
│   │   │   ├── state.py           # 状态定义
│   │   │   ├── tools/             # LangChain 工具
│   │   │   └── utils.py           # 工具函数
│   │   ├── api/                   # API 路由
│   │   │   └── v1/
│   │   │       ├── auth.py        # 认证接口
│   │   │       ├── chat.py        # 聊天接口
│   │   │       ├── sessions.py    # 会话接口
│   │   │       └── knowledge.py   # 知识库接口
│   │   ├── models/                # 数据库模型
│   │   │   ├── user.py            # 用户模型
│   │   │   ├── session.py         # 会话模型
│   │   │   ├── message.py         # 消息模型
│   │   │   └── knowledge.py       # 知识库模型
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # 业务逻辑
│   │   │   ├── llm_service.py     # LLM 服务
│   │   │   ├── document_service.py # 文档服务
│   │   │   ├── firecrawl_service.py # 案例搜索服务
│   │   │   ├── memory_service.py  # 记忆服务
│   │   │   └── session_service.py # 会话服务
│   │   ├── database.py            # 数据库配置
│   │   └── main.py                # 应用入口
│   ├── tests/                     # 测试
│   │   ├── agents/                # Agent 测试
│   │   ├── api/                   # API 测试
│   │   └── services/              # 服务测试
│   ├── alembic/                   # 数据库迁移
│   ├── data/                      # 数据文件
│   │   └── chroma/                # ChromaDB 数据
│   └── requirements.txt           # Python 依赖
│
├── frontend/                      # 前端应用
│   ├── src/
│   │   ├── api/                   # API 客户端
│   │   │   ├── client.ts          # HTTP 客户端
│   │   │   └── streamingClient.ts # SSE 客户端
│   │   ├── components/            # React 组件
│   │   │   ├── chat/              # 聊天组件
│   │   │   │   ├── ChatView.tsx   # 聊天视图
│   │   │   │   ├── MessageInput.tsx    # 输入框
│   │   │   │   ├── MessageBubble.tsx   # 消息气泡
│   │   │   │   ├── ThinkingIndicator.tsx # 思考状态
│   │   │   │   └── CaseSearchButton.tsx # 案例搜索按钮
│   │   │   ├── knowledge/         # 知识库组件
│   │   │   ├── sessions/          # 会话组件
│   │   │   ├── auth/              # 认证组件
│   │   │   ├── layout/            # 布局组件
│   │   │   └── ui/                # UI 组件
│   │   ├── stores/                # Zustand 状态管理
│   │   │   ├── authStore.ts       # 认证状态
│   │   │   └── chatStore.ts       # 聊天状态
│   │   ├── utils/                 # 工具函数
│   │   ├── App.tsx                # 应用入口
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
└── docs/                          # 文档
```

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL
- 阿里云 DashScope API Key
- Firecrawl API Key (可选，用于案例搜索)

### 后端启动

```bash
cd backend

# 配置环境变量
cp .env.example .env
# 编辑 .env，添加必要的 API Keys

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload
```

后端运行在: http://localhost:8000
API 文档: http://localhost:8000/docs

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在: http://localhost:5173

### 环境变量配置

**后端 (.env)**:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/legal_consultation
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/legal_consultation

# DashScope / Qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3

# Firecrawl (案例搜索)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# ChromaDB
CHROMA_DB_PATH=./data/chroma
CHROMA_COLLECTION_NAME=legal_knowledge

# App
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
CORS_ORIGINS=http://localhost:5173

# Auth
SECRET_KEY=your-secure-secret-key-min-32-characters-long
JWT_EXPIRE_DAYS=7

# Memory
ENABLE_MEMORY_EXTRACTION=true
```

**前端 (.env)**:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

## API 文档

### 认证接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 获取当前用户 |

### 聊天接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/chat` | 发送消息（非流式） |
| POST | `/api/v1/chat/stream` | 发送消息（SSE 流式） |

### 会话接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/sessions` | 获取会话列表 |
| GET | `/api/v1/sessions/{id}` | 获取会话详情 |
| DELETE | `/api/v1/sessions/{id}` | 删除会话 |
| POST | `/api/v1/sessions/{id}/end` | 结束会话并生成摘要 |

### 知识库接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/knowledge/documents` | 获取文档列表 |
| POST | `/api/v1/knowledge/documents/upload` | 上传文档 |
| DELETE | `/api/v1/knowledge/documents/{id}` | 删除文档 |
| GET | `/api/v1/knowledge/stats` | 获取统计信息 |

### SSE 流式事件

发送消息到 `/api/v1/chat/stream` 返回以下事件：

```javascript
// session_id - 会话 ID
{ event: "session_id", data: { session_id: "xxx" } }

// intent - 用户意图
{ event: "intent", data: { intent: "legal_consultation" } }

// context - 检索到的知识库
{ event: "context", data: { sources: [...] } }

// token - 响应片段
{ event: "token", data: { chunk: "你好", full_response: "你好" } }

// end - 响应完成
{ event: "end", data: { response: "完整回复" } }

// error - 错误
{ event: "error", data: { error: "错误信息" } }
```

## 核心功能说明

### 意图路由系统

系统根据用户输入自动识别意图并路由到相应的处理节点：

- **legal_consultation**: 法律咨询 → RAG检索 → 生成回复
- **case_search**: 案例搜索 → Firecrawl搜索 → 格式化结果
- **greeting**: 问候语 → 友好回复
- **general_chat**: 一般对话 → 直接生成回复

### 记忆系统

为认证用户提供个性化体验：

- **短期记忆**: 最近几次会话的上下文
- **长期记忆**: 提取的用户偏好和重要信息
- **自动摘要**: 会话结束时自动生成摘要

### 案例搜索

点击"🔍 搜索相关案例"按钮：
1. 弹出对话框，预填充建议关键词
2. 用户可自定义搜索关键词
3. 后端使用 Firecrawl 搜索真实法律案例
4. 返回格式化的案例结果

## 测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=app --cov-report=html
```

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并生成覆盖率
npm run test:coverage

# 类型检查
npm run type-check

# Lint
npm run lint
```

## 部署

### 生产环境配置

1. 修改 `.env` 中的配置：
   - 设置 `APP_DEBUG=false`
   - 使用生产数据库连接
   - 配置安全的 `SECRET_KEY`

2. 构建前端：
   ```bash
   cd frontend
   npm run build
   ```

3. 使用 Nginx 托管前端静态文件并代理后端 API

### Docker 部署（推荐）

详细的 Docker 配置可以自行创建或参考相关文档。

## 常见问题

### Q: 如何获取 DashScope API Key?

A: 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)，注册账号并创建 API Key。

### Q: 如何获取 Firecrawl API Key?

A: 访问 [Firecrawl 官网](https://www.firecrawl.dev/)，注册账号并创建 API Key。案例搜索功能可选，不配置也能正常使用其他功能。

### Q: 支持哪些文档格式?

A: 目前支持 PDF、DOCX 和 TXT 格式。

### Q: 如何切换到生产数据库?

A: 修改 `.env` 中的 `DATABASE_URL` 为 PostgreSQL 连接字符串。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

