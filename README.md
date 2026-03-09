# 法律咨询助手 (Legal Consultation Assistant)

> 基于 DashScope Qwen + LangGraph 的 AI 法律咨询平台

AI-powered legal consultation platform with RAG-based responses, streaming chat, and knowledge base management.

## 功能特性

### 💬 智能对话
- **多轮对话**: 支持上下文理解的多轮法律咨询
- **流式响应**: SSE 实时流式输出，提供更流畅的交互体验
- **意图识别**: 自动识别用户意图（法律咨询/问候/一般对话）
- **RAG 检索**: 基于向量检索的法律知识库问答
- **思考状态**: 实时显示 AI 处理状态（理解/检索/生成）

### 📚 知识库管理
- **文档上传**: 支持 PDF、DOCX、TXT 格式
- **智能分块**: 自动文档分块和向量化
- **分类管理**: 法律法规、案例分析、合同范本、司法解释
- **批量操作**: 文档列表、搜索、筛选、删除
- **统计面板**: 文档数量、知识块统计、分类分布

### 📊 会话管理
- **会话历史**: 完整的对话历史记录
- **自动摘要**: AI 自动生成会话摘要
- **快速导航**: 会话列表和快速切换
- **对话导出**: 导出对话为 TXT 文件

### 📱 响应式设计
- **移动端适配**: 完美的移动端体验
- **触摸优化**: 针对触摸交互的优化
- **侧边栏抽屉**: 移动端友好的导航

## 技术架构

### 后端技术栈
- **框架**: FastAPI + Python 3.11+
- **LLM**: 阿里云 DashScope Qwen (qwen-plus/qwen-turbo)
- **Agent**: LangGraph (多节点编排)
- **向量存储**: ChromaDB + DashScope text-embedding-v3
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **异步**: asyncio + aiosqlite

### 前端技术栈
- **框架**: React 18 + TypeScript + Vite
- **状态管理**: Zustand
- **路由**: React Router v6
- **HTTP**: Axios
- **图标**: Lucide React
- **样式**: CSS Variables (类 Tailwind)

### Agent 节点流程

```
用户输入 → 意图路由 → RAG 检索 → 响应生成
           ↓
       (legal_consultation)
           ↓
      检索知识库
           ↓
      生成回复
```

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- 阿里云 DashScope API Key

### 后端启动

```bash
cd backend

# 配置环境变量
cp .env.example .env
# 编辑 .env，添加 DASHSCOPE_API_KEY

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python create_tables.py

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
DATABASE_URL=sqlite+aiosqlite:///./data/legal.db
DATABASE_URL_SYNC=sqlite:///./data/legal.db

# DashScope / Qwen
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

**前端 (.env)**:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

## API 文档

### 聊天接口

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/chat` | 发送消息（非流式） |
| POST | `/api/v1/chat/stream` | 发送消息（SSE 流式） |
| GET | `/api/v1/chat/sessions/{id}/summary` | 获取会话摘要 |
| POST | `/api/v1/chat/sessions/{id}/summary/regenerate` | 重新生成摘要 |

### 会话接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/sessions` | 获取会话列表 |
| GET | `/api/v1/sessions/{id}` | 获取会话详情 |
| DELETE | `/api/v1/sessions/{id}` | 删除会话 |

### 知识库接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/knowledge/documents` | 获取文档列表 |
| POST | `/api/v1/knowledge/documents` | 创建文档元数据 |
| POST | `/api/v1/knowledge/documents/upload` | 上传文档 |
| GET | `/api/v1/knowledge/documents/{id}` | 获取文档详情 |
| PUT | `/api/v1/knowledge/documents/{id}` | 更新文档 |
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

## 项目结构

```
dialog_chat_room/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── agents/         # LangGraph agents
│   │   ├── api/            # API 路由
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # 业务逻辑
│   │   ├── database.py     # 数据库配置
│   │   └── main.py         # 应用入口
│   ├── tests/              # 测试
│   ├── data/               # 数据文件
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── components/    # React 组件
│   │   │   ├── chat/      # 聊天组件
│   │   │   ├── knowledge/ # 知识库组件
│   │   │   ├── sessions/  # 会话组件
│   │   │   ├── layout/    # 布局组件
│   │   │   └── ui/        # UI 组件
│   │   ├── stores/        # Zustand 状态管理
│   │   ├── App.tsx        # 应用入口
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/                   # 文档
└── README.md
```

## 更多文档

- [版本计划](./docs/ROADMAP.md) - 功能版本规划和未来扩展
- [扩展点文档](./docs/EXTENSIONS.md) - 系统扩展接口和开发指南
- [部署指南](./docs/DEPLOYMENT.md) - 详细部署文档
- [测试指南](./docs/TESTING.md) - 测试文档和最佳实践

## 开发指南

### 添加新的 Agent 节点

1. 在 `app/agents/nodes.py` 中定义节点函数
2. 在 `app/agents/graph.py` 中添加到工作流
3. 更新状态定义（如需要）

### 添加新的 API 端点

1. 在 `app/api/v1/` 中创建路由文件
2. 在 `app/api/v1/__init__.py` 中注册路由
3. 添加相应的 schema 和 service

### 添加新的前端页面

1. 在 `src/components/` 中创建页面组件
2. 在 `App.tsx` 中添加路由
3. 更新 Navigation 组件（如需要）

## 测试

详细测试指南请参阅: [docs/TESTING.md](./docs/TESTING.md)

### 后端测试

```bash
cd backend

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_knowledge_api.py -v

# 运行测试并查看覆盖率
pytest tests/ --cov=app --cov-report=html
```

**测试覆盖：**
- 知识库 API 测试 (18 tests)
- SSE 流式响应测试 (10 tests)
- 摘要服务测试 (9 tests)

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并监听变化
npm test -- --watch

# 运行测试 UI 模式
npm run test:ui

# 运行测试并生成覆盖率
npm run test:coverage

# 类型检查
npm run type-check

# Lint
npm run lint
```

**测试覆盖：**
- UI 组件测试 (Button, Skeleton, Alert, Transition)
- 聊天组件测试 (MessageBubble, ThinkingIndicator)
- 知识库组件测试 (StatsPanel, DocumentCard)

### 测试文件结构

```
backend/tests/
├── test_knowledge_api.py      # 知识库 API 测试
├── test_streaming.py           # SSE 流式响应测试
└── test_summary_service.py     # 摘要服务测试

frontend/src/
├── test/
│   ├── setup.ts               # 测试设置
│   └── test-utils.tsx         # 测试工具
├── components/
│   ├── ui/                    # UI 组件测试
│   ├── chat/                  # 聊天组件测试
│   └── knowledge/             # 知识库组件测试
```

## 部署

### 使用 Docker Compose（推荐）

```bash
docker-compose up -d
```

### 手动部署

详细部署指南请参阅: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

## 常见问题

### Q: 如何获取 DashScope API Key?

A: 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)，注册账号并创建 API Key。

### Q: 支持哪些文档格式?

A: 目前支持 PDF、DOCX 和 TXT 格式。

### Q: 如何切换到生产数据库?

A: 修改 `.env` 中的 `DATABASE_URL` 为 PostgreSQL 连接字符串。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v0.2.0 (2026-03-09)
- ✅ 完整的前端测试基础设施 (Vitest + Testing Library)
- ✅ UI 组件测试套件 (Button, Skeleton, Alert, Transition)
- ✅ 聊天组件测试 (MessageBubble, ThinkingIndicator)
- ✅ 知识库组件测试 (StatsPanel, DocumentCard)
- ✅ 测试文档和最佳实践指南
- ✅ 覆盖率配置和 CI/CD 集成指南

### v0.1.0 (2026-03-09)
- ✅ 基础对话功能
- ✅ SSE 流式响应
- ✅ 知识库管理
- ✅ 会话自动摘要
- ✅ 响应式设计
- ✅ 后端测试覆盖 (37 tests)
- ✅ 部署文档和指南

## 开发路线图

### 即将推出
- [ ] API 集成测试
- [ ] E2E 测试 (Playwright)
- [ ] 对话导出功能
- [ ] 用户认证系统
- [ ] 多语言支持
