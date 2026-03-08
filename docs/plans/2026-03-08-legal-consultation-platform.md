# Legal Consultation Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an AI-powered legal consultation platform with RAG-based responses, session management, and knowledge base admin panel.

**Architecture:** Monolithic FastAPI backend with modular LangGraph agents, React TypeScript frontend, PostgreSQL for sessions, ChromaDB for vector search, OpenAI for LLM/embeddings.

**Tech Stack:** FastAPI, PostgreSQL, ChromaDB, LangChain, LangGraph, OpenAI GPT-4, React, TypeScript

---

## Phase 1: Project Setup & Infrastructure

### Task 1.1: Backend Project Structure

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/README.md`

**Step 1: Create pyproject.toml**

Create `backend/pyproject.toml`:

```toml
[project]
name = "legal-consultation-backend"
version = "0.1.0"
description = "Legal consultation platform backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.5",
    "langgraph>=0.0.20",
    "chromadb>=0.4.22",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "pypdf>=4.0.0",
    "python-docx>=1.1.0",
    "structlog>=24.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

**Step 2: Create .env.example**

Create `backend/.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/legal_consultation
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/legal_consultation

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ChromaDB
CHROMA_DB_PATH=./data/chroma

# App
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
CORS_ORIGINS=http://localhost:5173

# Summary Settings
SUMMARY_MESSAGE_THRESHOLD=10
SUMMARY_TOKEN_THRESHOLD=8000
```

**Step 3: Create README.md**

Create `backend/README.md`:

```markdown
# Legal Consultation Backend

FastAPI backend with LangGraph agents for legal consultation.

## Setup

```bash
# Install dependencies
uv sync

# Copy environment
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Running Tests

```bash
pytest tests/
```
```

**Step 4: Commit**

```bash
cd backend
git add pyproject.toml .env.example README.md
git commit -m "feat: add backend project structure and dependencies"
```

---

### Task 1.2: Backend Application Structure

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/logger.py`

**Step 1: Create config.py**

Create `backend/app/config.py`:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"

    # ChromaDB
    chroma_db_path: str = "./data/chroma"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    cors_origins: str = "http://localhost:5173"

    # Summary
    summary_message_threshold: int = 10
    summary_token_threshold: int = 8000

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 2: Create logger.py**

Create `backend/app/logger.py`:

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
)

log = structlog.get_logger()
```

**Step 3: Create main.py**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.logger import log

settings = get_settings()

app = FastAPI(
    title="Legal Consultation API",
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    log.info("application_started", port=settings.app_port)


@app.on_event("shutdown")
async def shutdown_event():
    log.info("application_shutdown")
```

**Step 4: Create empty __init__.py**

Create `backend/app/__init__.py` as empty file.

**Step 5: Commit**

```bash
cd backend
git add app/__init__.py app/main.py app/config.py app/logger.py
git commit -m "feat: add app configuration, logger, and main entry point"
```

---

### Task 1.3: Database Setup

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/001_initial.py`

**Step 1: Create database.py**

Create `backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.app_debug)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Step 2: Create alembic.ini**

Create `backend/alembic.ini`:

```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
sqlalchemy.url = driver://user:pass@localhost/dbname

[log]
path = alembic.log
```

**Step 3: Create alembic/env.py**

Create `backend/alembic/env.py`:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.config import get_settings
from app.database import Base
from app.models import session, message, knowledge  # noqa: F401

settings = get_settings()
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    return settings.database_url_sync


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Create initial migration**

Create `backend/alembic/versions/001_initial.py`:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=500), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_session_id"), "messages", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_session_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_table("knowledge_documents")
    op.drop_table("sessions")
```

**Step 5: Create models directory**

Create `backend/app/models/__init__.py`:

```python
from app.models.session import Session  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.knowledge import KnowledgeDocument  # noqa: F401
```

**Step 6: Commit**

```bash
cd backend
git add database.py alembic.ini alembic/ app/models/__init__.py
git commit -m "feat: add database configuration and initial migrations"
```

---

### Task 1.4: Frontend Project Structure

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/README.md`

**Step 1: Create package.json**

Create `frontend/package.json`:

```json
{
  "name": "legal-consultation-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

**Step 2: Create tsconfig.json**

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": "./src",
    "paths": {
      "@/*": ["*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Step 3: Create vite.config.ts**

Create `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

**Step 4: Create index.html**

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>法律咨询助手</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 5: Create tsconfig.node.json**

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

**Step 6: Create README.md**

Create `frontend/README.md`:

```markdown
# Legal Consultation Frontend

React + TypeScript frontend for legal consultation platform.

## Setup

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```
```

**Step 7: Commit**

```bash
cd frontend
git add package.json tsconfig.json tsconfig.node.json vite.config.ts index.html README.md
git commit -m "feat: add frontend project structure"
```

---

## Phase 2: Backend - Database Models

### Task 2.1: Session Model

**Files:**
- Create: `backend/app/models/session.py`
- Test: `backend/tests/models/test_session.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_session.py`:

```python
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.database import Base


async def test_create_session(db_session: AsyncSession):
    session = Session(title="Test Session")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.id is not None
    assert session.title == "Test Session"
    assert session.message_count == 0
    assert session.created_at is not None
    assert session.updated_at is not None


async def test_session_defaults(db_session: AsyncSession):
    session = Session()
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.title is None
    assert session.message_count == 0
    assert session.summary is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_session.py -v
# Expected: ImportError or failure - model doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/models/session.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    summary = Column(Text, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/models/test_session.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
cd backend
git add app/models/session.py tests/models/test_session.py
git commit -m "feat: add Session model with tests"
```

---

### Task 2.2: Message Model

**Files:**
- Create: `backend/app/models/message.py`
- Test: `backend/tests/models/test_message.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_message.py`:

```python
import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.models.message import Message


async def test_create_message(db_session: AsyncSession):
    session = Session(title="Test")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    message = Message(
        session_id=session.id,
        role="user",
        content="Hello, this is a test message",
        metadata={"source": "test"}
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)

    assert message.id is not None
    assert message.session_id == session.id
    assert message.role == "user"
    assert message.content == "Hello, this is a test message"
    assert message.metadata == {"source": "test"}


async def test_message_role_validation(db_session: AsyncSession, session: Session):
    valid_roles = ["user", "assistant", "system"]

    for role in valid_roles:
        message = Message(
            session_id=session.id,
            role=role,
            content=f"Message as {role}"
        )
        db_session.add(message)
        await db_session.commit()

    messages = await Message.get_by_session(db_session, session.id)
    assert len(messages) == 3
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_message.py -v
# Expected: ImportError - model doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/models/message.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="cascade"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    metadata = Column(JSONB, nullable=True)

    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_session_id", "session_id"),
    )

    @classmethod
    async def get_by_session(cls, db_session, session_id: uuid.UUID):
        from sqlalchemy import select
        result = await db_session.execute(
            select(cls).where(cls.session_id == session_id).order_by(cls.created_at)
        )
        return result.scalars().all()
```

**Step 4: Update Session model for relationship**

Modify `backend/app/models/session.py`:

```python
from sqlalchemy.orm import relationship
# ... (keep existing imports)

class Session(Base):
    # ... (keep existing columns)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
```

**Step 5: Run test to verify it passes**

```bash
cd backend
pytest tests/models/test_message.py -v
# Expected: PASS
```

**Step 6: Commit**

```bash
cd backend
git add app/models/message.py app/models/session.py tests/models/test_message.py
git commit -m "feat: add Message model with relationship and tests"
```

---

### Task 2.3: Knowledge Document Model

**Files:**
- Create: `backend/app/models/knowledge.py`
- Test: `backend/tests/models/test_knowledge.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_knowledge.py`:

```python
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeDocument


async def test_create_knowledge_document(db_session: AsyncSession):
    doc = KnowledgeDocument(
        title="Contract Law Basics",
        category="law",
        source="https://example.com/contract-law"
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    assert doc.id is not None
    assert doc.title == "Contract Law Basics"
    assert doc.category == "law"
    assert doc.source == "https://example.com/contract-law"
    assert doc.chunk_count == 0


async def test_document_categories(db_session: AsyncSession):
    categories = ["law", "case", "contract", "interpretation"]

    for i, category in enumerate(categories):
        doc = KnowledgeDocument(
            title=f"Document {i}",
            category=category
        )
        db_session.add(doc)
        await db_session.commit()

    from sqlalchemy import select, func
    result = await db_session.execute(
        select(func.count(KnowledgeDocument.id))
    )
    count = result.scalar()
    assert count == len(categories)
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/models/test_knowledge.py -v
# Expected: ImportError - model doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/models/knowledge.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # 'law' | 'case' | 'contract' | 'interpretation'
    source = Column(String(500), nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    VALID_CATEGORIES = {"law", "case", "contract", "interpretation"}
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/models/test_knowledge.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
cd backend
git add app/models/knowledge.py tests/models/test_knowledge.py
git commit -m "feat: add KnowledgeDocument model with tests"
```

---

## Phase 3: Backend - Core APIs

### Task 3.1: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/session.py`
- Create: `backend/app/schemas/message.py`
- Create: `backend/app/schemas/knowledge.py`

**Step 1: Create session schemas**

Create `backend/app/schemas/session.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SessionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: str = Field(..., max_length=255)


class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    id: UUID
    title: Optional[str]
    created_at: datetime
    summary: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True
```

**Step 2: Create message schemas**

Create `backend/app/schemas/message.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List


class MessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    session_id: Optional[UUID] = None


class MessageResponse(MessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str = Field(..., min_length=1)


class ChatStreamChunk(BaseModel):
    type: str  # "token" | "error" | "done" | "citation"
    data: str | Dict[str, Any]
```

**Step 3: Create knowledge schemas**

Create `backend/app/schemas/knowledge.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class KnowledgeDocumentBase(BaseModel):
    title: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=500)


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: UUID
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)
    category: Optional[str] = None


class SearchResult(BaseModel):
    text: str
    score: float
    metadata: dict
```

**Step 4: Create __init__.py**

Create `backend/app/schemas/__init__.py`:

```python
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.schemas.message import MessageCreate, MessageResponse, ChatRequest, ChatStreamChunk
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentResponse, SearchRequest, SearchResult
```

**Step 5: Commit**

```bash
cd backend
git add app/schemas/__init__.py app/schemas/*.py
git commit -m "feat: add Pydantic schemas for API validation"
```

---

### Task 3.2: Session CRUD Operations

**Files:**
- Create: `backend/app/services/session_service.py`
- Test: `backend/tests/services/test_session_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_session_service.py`:

```python
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionUpdate


@pytest.mark.asyncio
async def test_create_session(db_session: AsyncSession):
    service = SessionService(db_session)
    data = SessionCreate(title="Test Session")

    session = await service.create_session(data)

    assert session.id is not None
    assert session.title == "Test Session"
    assert session.message_count == 0


@pytest.mark.asyncio
async def test_list_sessions(db_session: AsyncSession):
    service = SessionService(db_session)

    for i in range(3):
        await service.create_session(SessionCreate(title=f"Session {i}"))

    sessions = await service.list_sessions()

    assert len(sessions) == 3
    assert all(s.id is not None for s in sessions)


@pytest.mark.asyncio
async def test_get_session(db_session: AsyncSession):
    service = SessionService(db_session)
    created = await service.create_session(SessionCreate(title="Test"))

    session = await service.get_session(created.id)

    assert session is not None
    assert session.id == created.id
    assert session.title == "Test"


@pytest.mark.asyncio
async def test_update_session(db_session: AsyncSession):
    service = SessionService(db_session)
    created = await service.create_session(SessionCreate(title="Old Title"))

    updated = await service.update_session(created.id, SessionUpdate(title="New Title"))

    assert updated.title == "New Title"


@pytest.mark.asyncio
async def test_delete_session(db_session: AsyncSession):
    service = SessionService(db_session)
    created = await service.create_session(SessionCreate(title="ToDelete"))

    await service.delete_session(created.id)

    session = await service.get_session(created.id)
    assert session is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_session_service.py -v
# Expected: ImportError - service doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/services/session_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, data: SessionCreate) -> SessionResponse:
        session = Session(title=data.title)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return SessionResponse.model_validate(session)

    async def list_sessions(self) -> List[SessionResponse]:
        result = await self.db.execute(
            select(Session).order_by(Session.updated_at.desc())
        )
        sessions = result.scalars().all()
        return [SessionResponse.model_validate(s) for s in sessions]

    async def get_session(self, session_id: UUID) -> SessionResponse | None:
        result = await self.db.execute(
            select(Session)
            .options(selectinload(Session.messages))
            .where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        return SessionResponse.model_validate(session) if session else None

    async def update_session(self, session_id: UUID, data: SessionUpdate) -> SessionResponse:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        session.title = data.title
        await self.db.commit()
        await self.db.refresh(session)
        return SessionResponse.model_validate(session)

    async def delete_session(self, session_id: UUID) -> None:
        await self.db.execute(delete(Session).where(Session.id == session_id))
        await self.db.commit()

    async def increment_message_count(self, session_id: UUID) -> None:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            session.message_count += 1
            await self.db.commit()
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_session_service.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
cd backend
git add app/services/session_service.py tests/services/test_session_service.py
git commit -m "feat: add Session CRUD service with tests"
```

---

### Task 3.3: Session API Routes

**Files:**
- Create: `backend/app/api/v1/sessions.py`
- Modify: `backend/app/main.py`

**Step 1: Create sessions router**

Create `backend/app/api/__init__.py` as empty file.

Create `backend/app/api/v1/__init__.py`:

```python
from fastapi import APIRouter
from app.api.v1 import sessions, chat, knowledge

api_router = APIRouter(prefix="/api/v1")
api_router.include_routersessions.router, tags=["sessions"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(knowledge.router, tags=["knowledge"])
```

Create `backend/app/api/v1/sessions.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new session"""
    service = SessionService(db)
    return await service.create_session(data)


@router.get("", response_model=list[SessionListResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db)
):
    """List all sessions"""
    service = SessionService(db)
    return await service.list_sessions()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a session by ID with messages"""
    service = SessionService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Rename a session"""
    service = SessionService(db)
    try:
        return await service.update_session(session_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a session"""
    service = SessionService(db)
    await service.delete_session(session_id)
    return {"message": "Session deleted"}
```

**Step 2: Update main.py**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.logger import log
from app.api.v1 import api_router

settings = get_settings()

app = FastAPI(
    title="Legal Consultation API",
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    log.info("application_started", port=settings.app_port)


@app.on_event("shutdown")
async def shutdown_event():
    log.info("application_shutdown")
```

**Step 3: Create placeholder routers**

Create `backend/app/api/v1/chat.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])
```

Create `backend/app/api/v1/knowledge.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
```

**Step 4: Test endpoints manually**

```bash
cd backend
# Start server
uvicorn app.main:app --reload

# In another terminal, test:
curl -X GET http://localhost:8000/api/v1/sessions
curl -X POST http://localhost:8000/api/v1/sessions -H "Content-Type: application/json" -d '{"title":"Test"}'
```

**Step 5: Commit**

```bash
cd backend
git add app/api/ app/main.py
git commit -m "feat: add session API routes"
```

---

### Task 3.4: Message CRUD Operations

**Files:**
- Create: `backend/app/services/message_service.py`
- Test: `backend/tests/services/test_message_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_message_service.py`:

```python
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.message_service import MessageService
from app.services.session_service import SessionService
from app.schemas.message import MessageCreate


@pytest.mark.asyncio
async def test_create_message(db_session: AsyncSession):
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"})

    message_service = MessageService(db_session)
    data = MessageCreate(session_id=session.id, role="user", content="Hello")

    message = await message_service.create_message(data)

    assert message.id is not None
    assert message.content == "Hello"


@pytest.mark.asyncio
async def test_get_messages_by_session(db_session: AsyncSession):
    session_service = SessionService(db_session)
    session = await session_service.create_session({"title": "Test"})

    message_service = MessageService(db_session)
    await message_service.create_message(MessageCreate(session_id=session.id, role="user", content="Hi"))
    await message_service.create_message(MessageCreate(session_id=session.id, role="assistant", content="Hello"))

    messages = await message_service.get_messages_by_session(session.id)

    assert len(messages) == 2
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_message_service.py -v
# Expected: ImportError - service doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/services/message_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, data: MessageCreate) -> MessageResponse:
        message = Message(
            session_id=data.session_id,
            role=data.role,
            content=data.content
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return MessageResponse.model_validate(message)

    async def get_messages_by_session(self, session_id: UUID) -> List[MessageResponse]:
        messages = await Message.get_by_session(self.db, session_id)
        return [MessageResponse.model_validate(m) for m in messages]
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_message_service.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
cd backend
git add app/services/message_service.py tests/services/test_message_service.py
git commit -m "feat: add Message CRUD service with tests"
```

---

## Phase 4: Backend - Knowledge Base

### Task 4.1: ChromaDB Setup

**Files:**
- Create: `backend/app/services/chroma_service.py`
- Create: `backend/app/services/embedding_service.py`
- Test: `backend/tests/services/test_chroma_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_chroma_service.py`:

```python
import pytest
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_add_documents():
    chroma = ChromaService()
    embedding = EmbeddingService()

    documents = [
        {"text": "Contract law governs agreements", "metadata": {"category": "law", "title": "Contracts 101"}},
        {"text": "Criminal law deals with crimes", "metadata": {"category": "law", "title": "Criminal Law"}},
    ]

    embeddings = await embedding.embed_texts([d["text"] for d in documents])
    ids = await chroma.add_documents(documents, embeddings)

    assert len(ids) == 2


@pytest.mark.asyncio
async def test_search_documents():
    chroma = ChromaService()
    embedding = EmbeddingService()

    query = "What is contract law?"
    query_embedding = await embedding.embed_query(query)

    results = await chroma.search(query_embedding, n_results=2)

    assert len(results) >= 0
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_chroma_service.py -v
# Expected: ImportError - services don't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/services/embedding_service.py`:

```python
from langchain_openai import OpenAIEmbeddings
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key
        )

    async def embed_query(self, text: str) -> list[float]:
        return await self.embeddings.aembed_query(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self.embeddings.aembed_documents(texts)
```

Create `backend/app/services/chroma_service.py`:

```python
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
from app.config import get_settings

settings = get_settings()


class ChromaService:
    COLLECTION_NAME = "legal_knowledge"

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._get_or_create_collection()

    def _get_or_create_collection(self):
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> List[str]:
        ids = [f"doc_{i}_{hash(doc['text'])}" for i, doc in enumerate(documents)]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        return ids

    async def search(self, query_embedding: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return [
            {
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]  # Convert distance to similarity
            }
            for i in range(len(results["ids"][0]))
        ]

    async def delete_by_document_id(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_chroma_service.py -v
# Expected: PASS (requires OPENAI_API_KEY set)
```

**Step 5: Commit**

```bash
cd backend
git add app/services/chroma_service.py app/services/embedding_service.py tests/services/test_chroma_service.py
git commit -m "feat: add ChromaDB and embedding services with tests"
```

---

### Task 4.2: Document Processing

**Files:**
- Create: `backend/app/services/document_processor.py`
- Test: `backend/tests/services/test_document_processor.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_document_processor.py`:

```python
import pytest
from app.services.document_processor import DocumentProcessor


@pytest.mark.asyncio
async def test_chunk_text():
    processor = DocumentProcessor()

    text = "This is sentence one. This is sentence two. This is sentence three. " * 10
    chunks = processor.chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert all(len(c) > 0 for c in chunks)


@pytest.mark.asyncio
async def test_extract_text_from_pdf(tmp_path):
    # This requires a sample PDF file
    processor = DocumentProcessor()
    # Test with actual file in integration tests
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_document_processor.py -v
# Expected: ImportError - service doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/services/document_processor.py`:

```python
from typing import List
import pypdf
from docx import Document as DocxDocument


class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind("。")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)
                if break_point > chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap if end < len(text) else end

        return [c for c in chunks if len(c) > 10]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        doc = DocxDocument(docx_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    async def process_document(
        self,
        file_path: str,
        title: str,
        category: str,
        source: str = None
    ) -> dict:
        # Extract text based on file type
        if file_path.endswith(".pdf"):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith(".docx"):
            text = self.extract_text_from_docx(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

        # Chunk the text
        chunks = self.chunk_text(text)

        return {
            "title": title,
            "category": category,
            "source": source,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_document_processor.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
cd backend
git add app/services/document_processor.py tests/services/test_document_processor.py
git commit -m "feat: add document processor with chunking and text extraction"
```

---

### Task 4.3: Knowledge Service

**Files:**
- Create: `backend/app/services/knowledge_service.py`
- Test: `backend/tests/services/test_knowledge_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_knowledge_service.py`:

```python
import pytest
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import KnowledgeDocumentCreate


@pytest.mark.asyncio
async def test_upload_document(tmp_path, db_session: AsyncSession):
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test legal document about contracts.")

    service = KnowledgeService(db_session)
    data = KnowledgeDocumentCreate(
        title="Test Contract",
        category="contract",
        source=str(test_file)
    )

    result = await service.upload_document(data, str(test_file))

    assert result.id is not None
    assert result.chunk_count > 0


@pytest.mark.asyncio
async def test_search_knowledge(db_session: AsyncSession):
    service = KnowledgeService(db_session)

    results = await service.search("contract law", limit=5)

    assert isinstance(results, list)
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/services/test_knowledge_service.py -v
# Expected: ImportError - service doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/services/knowledge_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from app.models.knowledge import KnowledgeDocument
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentResponse, SearchResult
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.processor = DocumentProcessor()
        self.embedding = EmbeddingService()
        self.chroma = ChromaService()

    async def upload_document(
        self,
        data: KnowledgeDocumentCreate,
        file_path: str
    ) -> KnowledgeDocumentResponse:
        # Process document
        processed = await self.processor.process_document(
            file_path,
            data.title,
            data.category or "law",
            data.source
        )

        # Create database record
        doc = KnowledgeDocument(
            title=data.title,
            category=data.category,
            source=data.source,
            chunk_count=processed["chunk_count"]
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Generate embeddings and store in ChromaDB
        embeddings = await self.embedding.embed_texts(processed["chunks"])
        chroma_docs = [
            {
                "text": chunk,
                "metadata": {
                    "document_id": str(doc.id),
                    "category": data.category,
                    "title": data.title,
                    "chunk_index": i,
                    "source": data.source
                }
            }
            for i, chunk in enumerate(processed["chunks"])
        ]
        await self.chroma.add_documents(chroma_docs, embeddings)

        return KnowledgeDocumentResponse.model_validate(doc)

    async def list_documents(self) -> List[KnowledgeDocumentResponse]:
        result = await self.db.execute(
            select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
        )
        docs = result.scalars().all()
        return [KnowledgeDocumentResponse.model_validate(d) for d in docs]

    async def get_document(self, doc_id: UUID) -> KnowledgeDocumentResponse | None:
        result = await self.db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        return KnowledgeDocumentResponse.model_validate(doc) if doc else None

    async def delete_document(self, doc_id: UUID) -> None:
        await self.chroma.delete_by_document_id(str(doc_id))
        doc = await self.get_document(doc_id)
        if doc:
            await self.db.delete(doc)
            await self.db.commit()

    async def search(self, query: str, limit: int = 5, category: str = None) -> List[SearchResult]:
        query_embedding = await self.embedding.embed_query(query)
        results = await self.chroma.search(query_embedding, n_results=limit)

        if category:
            results = [r for r in results if r["metadata"].get("category") == category]

        return [SearchResult(**r) for r in results]
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/services/test_knowledge_service.py -v
# Expected: PASS (requires OPENAI_API_KEY set)
```

**Step 5: Commit**

```bash
cd backend
git add app/services/knowledge_service.py tests/services/test_knowledge_service.py
git commit -m "feat: add Knowledge service with upload, search, and CRUD"
```

---

### Task 4.4: Knowledge API Routes

**Files:**
- Modify: `backend/app/api/v1/knowledge.py`

**Step 1: Implement knowledge routes**

Modify `backend/app/api/v1/knowledge.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import tempfile
import os

from app.database import get_db
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    SearchRequest,
    SearchResult
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db)
):
    """List all knowledge documents"""
    service = KnowledgeService(db)
    return await service.list_documents()


@router.post("/upload", response_model=KnowledgeDocumentResponse)
async def upload_document(
    title: str = Form(...),
    category: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and embed a document"""
    service = KnowledgeService(db)

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        data = KnowledgeDocumentCreate(
            title=title,
            category=category,
            source=file.filename
        )
        return await service.upload_document(data, tmp_path)
    finally:
        os.unlink(tmp_path)


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and its embeddings"""
    service = KnowledgeService(db)
    await service.delete_document(document_id)
    return {"message": "Document deleted"}


@router.get("/search", response_model=list[SearchResult])
async def search_knowledge(
    q: str,
    limit: int = 10,
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Search the knowledge base"""
    service = KnowledgeService(db)
    return await service.search(q, limit=limit, category=category)
```

**Step 2: Test endpoints manually**

```bash
# Create a test file
echo "Contract law governs agreements between parties." > test.txt

# Upload
curl -X POST http://localhost:8000/api/v1/knowledge/upload \
  -F "title=Test Contract" \
  -F "category=contract" \
  -F "file=@test.txt"

# Search
curl "http://localhost:8000/api/v1/knowledge/search?q=contract&limit=5"
```

**Step 3: Commit**

```bash
cd backend
git add app/api/v1/knowledge.py
git commit -m "feat: add knowledge API routes for upload, search, and CRUD"
```

---

## Phase 5: Backend - LLM Integration

### Task 5.1: Intent Router Agent

**Files:**
- Create: `backend/app/agents/intent_router.py`
- Test: `backend/tests/agents/test_intent_router.py`

**Step 1: Write the failing test**

Create `backend/tests/agents/test_intent_router.py`:

```python
import pytest
from app.agents.intent_router import IntentRouter, IntentType


@pytest.mark.asyncio
async def test_route_legal_query():
    router = IntentRouter()

    result = await router.route("I need help with a contract dispute")

    assert result.intent == IntentType.LEGAL_CONSULTATION


@pytest.mark.asyncio
async def test_route_greeting():
    router = IntentRouter()

    result = await router.route("Hello")

    assert result.intent == IntentType.GREETING


@pytest.mark.asyncio
async def test_route_summary_request():
    router = IntentRouter()

    result = await router.route("Please summarize our conversation")

    assert result.intent == IntentType.SUMMARY_REQUEST
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/agents/test_intent_router.py -v
# Expected: ImportError - agent doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/agents/__init__.py` as empty file.

Create `backend/app/agents/intent_router.py`:

```python
from enum import Enum
from typing import NamedTuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings

settings = get_settings()


class IntentType(Enum):
    LEGAL_CONSULTATION = "legal_consultation"
    GREETING = "greeting"
    SUMMARY_REQUEST = "summary_request"
    CLARIFICATION_NEEDED = "clarification_needed"


class IntentResult(NamedTuple):
    intent: IntentType
    confidence: float
    reasoning: str


class IntentRouter:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a legal consultation chatbot.

Classify the user's query into one of these categories:
- legal_consultation: User is asking for legal information or advice
- greeting: User is greeting or saying hello/goodbye
- summary_request: User is asking for a summary of the conversation
- clarification_needed: Query is too vague and needs more context

Respond with just the category name."""),
            ("user", "{query}")
        ])

    async def route(self, query: str) -> IntentResult:
        chain = self.prompt | self.llm
        result = await chain.ainvoke({"query": query})
        intent_str = result.content.strip().lower()

        intent_map = {
            "legal_consultation": IntentType.LEGAL_CONSULTATION,
            "greeting": IntentType.GREETING,
            "summary_request": IntentType.SUMMARY_REQUEST,
            "clarification_needed": IntentType.CLARIFICATION_NEEDED
        }

        intent = intent_map.get(intent_str, IntentType.LEGAL_CONSULTATION)

        return IntentResult(
            intent=intent,
            confidence=0.8,  # Could use LLM with structured output for actual confidence
            reasoning=f"Classified as {intent.value}"
        )
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/agents/test_intent_router.py -v
# Expected: PASS (requires OPENAI_API_KEY set)
```

**Step 5: Commit**

```bash
cd backend
git add app/agents/intent_router.py tests/agents/test_intent_router.py
git commit -m "feat: add intent router agent with tests"
```

---

### Task 5.2: RAG Retriever Agent

**Files:**
- Create: `backend/app/agents/rag_retriever.py`
- Test: `backend/tests/agents/test_rag_retriever.py`

**Step 1: Write the failing test**

Create `backend/tests/agents/test_rag_retriever.py`:

```python
import pytest
from app.agents.rag_retriever import RAGRetriever


@pytest.mark.asyncio
async def test_retrieve_context():
    retriever = RAGRetriever()

    result = await retriever.retrieve("What are the requirements for a valid contract?")

    assert len(result.documents) > 0
    assert all(hasattr(doc, "text") for doc in result.documents)
    assert result.query == "What are the requirements for a valid contract?"


@pytest.mark.asyncio
async def test_format_context():
    retriever = RAGRetriever()

    formatted = retriever.format_context([
        {"text": "Contract text", "metadata": {"title": "Contract Law", "source": "example.com"}}
    ])

    assert "Contract text" in formatted
    assert "Contract Law" in formatted
    assert "example.com" in formatted
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/agents/test_rag_retriever.py -v
# Expected: ImportError - agent doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/agents/rag_retriever.py`:

```python
from typing import List, NamedTuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding_service import EmbeddingService
from app.services.chroma_service import ChromaService


class RetrievedDocument(NamedTuple):
    text: str
    source: str
    score: float
    metadata: dict


class RAGResult(NamedTuple):
    query: str
    documents: List[RetrievedDocument]
    formatted_context: str


class RAGRetriever:
    def __init__(self, db: AsyncSession, top_k: int = 5):
        self.db = db
        self.top_k = top_k
        self.embedding = EmbeddingService()
        self.chroma = ChromaService()

    async def retrieve(self, query: str, category: str = None) -> RAGResult:
        # Generate query embedding
        query_embedding = await self.embedding.embed_query(query)

        # Search ChromaDB
        raw_results = await self.chroma.search(query_embedding, n_results=self.top_k)

        # Convert to RetrievedDocument
        documents = [
            RetrievedDocument(
                text=r["text"],
                source=r["metadata"].get("source", "Unknown"),
                score=r["score"],
                metadata=r["metadata"]
            )
            for r in raw_results
        ]

        return RAGResult(
            query=query,
            documents=documents,
            formatted_context=self.format_context([d._asdict() for d in documents])
        )

    def format_context(self, documents: List[dict]) -> str:
        if not documents:
            return "没有找到相关的法律信息。"

        formatted_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            source = metadata.get("source") or metadata.get("title") or "Unknown"
            formatted_parts.append(
                f"[来源 {i}] {source}\n{doc['text']}"
            )

        return "\n\n".join(formatted_parts)
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/agents/test_rag_retriever.py -v
# Expected: PASS (requires OPENAI_API_KEY set)
```

**Step 5: Commit**

```bash
cd backend
git add app/agents/rag_retriever.py tests/agents/test_rag_retriever.py
git commit -m "feat: add RAG retriever agent with tests"
```

---

### Task 5.3: Response Generator Agent

**Files:**
- Create: `backend/app/agents/response_generator.py`
- Test: `backend/tests/agents/test_response_generator.py`

**Step 1: Write the failing test**

Create `backend/tests/agents/test_response_generator.py`:

```python
import pytest
from app.agents.response_generator import ResponseGenerator


@pytest.mark.asyncio
async def test_generate_response():
    generator = ResponseGenerator()

    result = await generator.generate(
        query="What is a contract?",
        context="Contract law governs agreements...",
        conversation_history=[]
    )

    assert result.content
    assert "contract" in result.content.lower() or "合同" in result.content


@pytest.mark.asyncio
async def test_generate_greeting():
    generator = ResponseGenerator()

    result = await generator.generate_greeting("Hello")

    assert result.content
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/agents/test_response_generator.py -v
# Expected: ImportError - agent doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/agents/response_generator.py`:

```python
from typing import List, NamedTuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

from app.config import get_settings

settings = get_settings()


class GeneratedResponse(NamedTuple):
    content: str
    sources: List[str]


class ResponseGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key
        )

        self.system_prompt = """你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 基于提供的法律知识库回答，引用相关法规
4. 回答要清晰、易懂，避免过度专业术语

参考信息：
{context}

请基于以上信息回答用户的问题。如果参考信息不足，请诚实地告知用户。"""

        self.legal_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{query}")
        ])

        self.greeting_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个友好的法律咨询助手。请用简洁、友好的方式回应用户的问候。"),
            ("human", "{query}")
        ])

    async def generate(
        self,
        query: str,
        context: str,
        conversation_history: List[tuple[str, str]] = None
    ) -> GeneratedResponse:
        chain = self.legal_prompt | self.llm
        result = await chain.ainvoke({
            "query": query,
            "context": context
        })

        # Extract sources from context
        sources = self._extract_sources(context)

        return GeneratedResponse(
            content=result.content,
            sources=sources
        )

    async def generate_greeting(self, query: str) -> GeneratedResponse:
        chain = self.greeting_prompt | self.llm
        result = await chain.ainvoke({"query": query})

        return GeneratedResponse(
            content=result.content,
            sources=[]
        )

    def _extract_sources(self, context: str) -> List[str]:
        # Extract [来源 N] from context
        import re
        pattern = r"\[来源 (\d+)\]\s*([^\n]+)"
        matches = re.findall(pattern, context)
        return [source for _, source in matches]

    async def generate_stream(self, query: str, context: str):
        """Generate streaming response"""
        chain = self.legal_prompt | self.llm
        async for chunk in chain.astream({"query": query, "context": context}):
            if chunk.content:
                yield chunk.content
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/agents/test_response_generator.py -v
# Expected: PASS (requires OPENAI_API_KEY set)
```

**Step 5: Commit**

```bash
cd backend
git add app/agents/response_generator.py tests/agents/test_response_generator.py
git commit -m "feat: add response generator agent with streaming support"
```

---

### Task 5.4: Summary Generator Agent

**Files:**
- Create: `backend/app/agents/summary_generator.py`
- Test: `backend/tests/agents/test_summary_generator.py`

**Step 1: Write the failing test**

Create `backend/tests/agents/test_summary_generator.py`:

```python
import pytest
from app.agents.summary_generator import SummaryGenerator


@pytest.mark.asyncio
async def test_generate_summary():
    generator = SummaryGenerator()

    conversation = [
        ("user", "I have a contract dispute"),
        ("assistant", "I can help with that..."),
        ("user", "What are my options?")
    ]

    summary = await generator.generate_summary(conversation)

    assert summary
    assert len(summary) > 0
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/agents/test_summary_generator.py -v
# Expected: ImportError - agent doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/agents/summary_generator.py`:

```python
from typing import List, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import get_settings

settings = get_settings()


class SummaryGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """请根据以下对话内容，生成简洁的咨询小结。

小结应包含：
1. 用户咨询的核心问题（1-2句话）
2. 提供的主要法律建议（要点列表）
3. 建议的后续行动（如果有）

请用清晰的中文格式输出。"""),
            ("human", "{conversation}")
        ])

    async def generate_summary(self, conversation: List[Tuple[str, str]]) -> str:
        # Format conversation
        formatted_conv = self._format_conversation(conversation)

        chain = self.prompt | self.llm
        result = await chain.ainvoke({"conversation": formatted_conv})

        return result.content

    def _format_conversation(self, conversation: List[Tuple[str, str]]) -> str:
        lines = []
        for role, content in conversation:
            role_name = "用户" if role == "user" else "助手"
            lines.append(f"{role_name}: {content}")
        return "\n\n".join(lines)

    async def should_generate_summary(
        self,
        message_count: int,
        estimated_tokens: int,
        time_since_last_summary: int = 0
    ) -> bool:
        """Determine if summary should be generated"""
        from app.config import get_settings
        settings = get_settings()

        return (
            message_count >= settings.summary_message_threshold or
            estimated_tokens >= settings.summary_token_threshold
        )
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/agents/test_summary_generator.py -v
# Expected: PASS (requires OPENAI_API_KEY set)
```

**Step 5: Commit**

```bash
cd backend
git add app/agents/summary_generator.py tests/agents/test_summary_generator.py
git commit -m "feat: add summary generator agent with threshold logic"
```

---

### Task 5.5: LangGraph Agent Orchestrator

**Files:**
- Create: `backend/app/agents/orchestrator.py`
- Test: `backend/tests/agents/test_orchestrator.py`

**Step 1: Write the failing test**

Create `backend/tests/agents/test_orchestrator.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.orchestrator import AgentState, LegalConsultationGraph


@pytest.mark.asyncio
async def test_process_legal_query(db_session: AsyncSession):
    graph = LegalConsultationGraph(db_session)

    state = AgentState(
        session_id="test-session",
        messages=[],
        user_message="What is contract law?",
        retrieved_context=[]
    )

    result = await graph.process(state)

    assert result.response
    assert len(result.messages) > 0


@pytest.mark.asyncio
async def test_process_greeting(db_session: AsyncSession):
    graph = LegalConsultationGraph(db_session)

    state = AgentState(
        session_id="test-session",
        messages=[],
        user_message="Hello",
        retrieved_context=[]
    )

    result = await graph.process(state)

    assert result.response
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/agents/test_orchestrator.py -v
# Expected: ImportError - orchestrator doesn't exist yet
```

**Step 3: Write minimal implementation**

Create `backend/app/agents/orchestrator.py`:

```python
from typing import List, TypedDict, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END

from app.agents.intent_router import IntentRouter, IntentType
from app.agents.rag_retriever import RAGRetriever, RAGResult
from app.agents.response_generator import ResponseGenerator, GeneratedResponse
from app.agents.summary_generator import SummaryGenerator


class AgentState(TypedDict):
    session_id: str
    messages: List[dict]
    user_message: str
    retrieved_context: List[dict]
    response: str
    intent: str
    sources: List[str]
    summary: str


class LegalConsultationGraph:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intent_router = IntentRouter()
        self.rag_retriever = RAGRetriever(db)
        self.response_generator = ResponseGenerator()
        self.summary_generator = SummaryGenerator()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("route_intent", self._route_intent)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("generate_greeting", self._generate_greeting)
        workflow.add_node("check_summary", self._check_summary)

        workflow.set_entry_point("route_intent")

        workflow.add_conditional_edges(
            "route_intent",
            self._should_retrieve,
            {
                "retrieve": "retrieve_context",
                "greeting": "generate_greeting"
            }
        )

        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("generate_response", "check_summary")
        workflow.add_edge("generate_greeting", "check_summary")
        workflow.add_edge("check_summary", END)

        return workflow.compile()

    async def _route_intent(self, state: AgentState) -> AgentState:
        result = await self.intent_router.route(state["user_message"])
        state["intent"] = result.intent.value
        return state

    def _should_retrieve(self, state: AgentState) -> str:
        if state.get("intent") == IntentType.GREETING.value:
            return "greeting"
        return "retrieve"

    async def _retrieve_context(self, state: AgentState) -> AgentState:
        result: RAGResult = await self.rag_retriever.retrieve(state["user_message"])
        state["retrieved_context"] = [d._asdict() for d in result.documents]
        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        context = self.rag_retriever.format_context(state["retrieved_context"])
        result: GeneratedResponse = await self.response_generator.generate(
            query=state["user_message"],
            context=context,
            conversation_history=state["messages"]
        )
        state["response"] = result.content
        state["sources"] = result.sources

        # Add messages
        state["messages"].append({"role": "user", "content": state["user_message"]})
        state["messages"].append({"role": "assistant", "content": result.content})

        return state

    async def _generate_greeting(self, state: AgentState) -> AgentState:
        result: GeneratedResponse = await self.response_generator.generate_greeting(state["user_message"])
        state["response"] = result.content
        state["sources"] = []

        state["messages"].append({"role": "user", "content": state["user_message"]})
        state["messages"].append({"role": "assistant", "content": result.content})

        return state

    async def _check_summary(self, state: AgentState) -> AgentState:
        message_count = len([m for m in state["messages"] if m["role"] == "user"])

        if await self.summary_generator.should_generate_summary(message_count, 0):
            # Convert messages to tuple format
            conv = [(m["role"], m["content"]) for m in state["messages"]]
            summary = await self.summary_generator.generate_summary(conv)
            state["summary"] = summary

        return state

    async def process(self, initial_state: AgentState) -> AgentState:
        result = await self.graph.ainvoke(initial_state)
        return result

    async def process_stream(self, initial_state: AgentState):
        """Process with streaming response"""
        # For now, just process normally and yield at end
        result = await self.process(initial_state)
        yield result
```

**Step 4: Run test to verify it passes**

```bash
cd backend
pytest tests/agents/test_orchestrator.py -v
# Expected: PASS (requires OPENAI_API_KEY set and knowledge base populated)
```

**Step 5: Commit**

```bash
cd backend
git add app/agents/orchestrator.py tests/agents/test_orchestrator.py
git commit -m "feat: add LangGraph agent orchestrator"
```

---

### Task 5.6: Chat API with Streaming

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Modify: `backend/app/services/message_service.py`

**Step 1: Update message service for async streaming support**

Modify `backend/app/services/message_service.py`:

```python
# Add to MessageService class
async def save_exchange(
    self,
    session_id: UUID,
    user_message: str,
    assistant_message: str,
    metadata: dict = None
) -> tuple[MessageResponse, MessageResponse]:
    """Save both user and assistant messages"""
    from datetime import datetime

    user_msg = Message(
        session_id=session_id,
        role="user",
        content=user_message
    )
    self.db.add(user_msg)

    asst_msg = Message(
        session_id=session_id,
        role="assistant",
        content=assistant_message,
        metadata=metadata or {}
    )
    self.db.add(asst_msg)

    await self.db.commit()
    await self.db.refresh(user_msg)
    await self.db.refresh(asst_msg)

    return (
        MessageResponse.model_validate(user_msg),
        MessageResponse.model_validate(asst_msg)
    )
```

**Step 2: Implement chat routes with streaming**

Modify `backend/app/api/v1/chat.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json

from app.database import get_db
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.agents.orchestrator import AgentState, LegalConsultationGraph
from app.schemas.message import ChatRequest
from app.logger import log

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send message and get response (non-streaming)"""
    session_service = SessionService(db)
    message_service = MessageService(db)

    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = request.session_id
    else:
        new_session = await session_service.create_session({"title": None})
        session_id = new_session.id

    # Get conversation history
    messages = await message_service.get_messages_by_session(session_id)

    # Process with agent
    graph = LegalConsultationGraph(db)
    state = AgentState(
        session_id=str(session_id),
        messages=[{"role": m.role, "content": m.content} for m in messages],
        user_message=request.message,
        retrieved_context=[],
        response="",
        intent="",
        sources=[],
        summary=""
    )

    result = await graph.process(state)

    # Save messages
    await message_service.save_exchange(
        session_id,
        request.message,
        result["response"],
        {"sources": result["sources"]}
    )

    # Update session title if first message
    if len(messages) == 0:
        await session_service.update_session(
            session_id,
            {"title": request.message[:50] + "..." if len(request.message) > 50 else request.message}
        )
    else:
        await session_service.increment_message_count(session_id)

    # Update summary if generated
    if result.get("summary"):
        # TODO: Save summary to session
        pass

    return {
        "session_id": session_id,
        "response": result["response"],
        "sources": result["sources"]
    }


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send message and stream response"""
    session_service = SessionService(db)
    message_service = MessageService(db)

    # Get or create session
    if request.session_id:
        session = await session_service.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = request.session_id
    else:
        new_session = await session_service.create_session({"title": None})
        session_id = new_session.id

    # Get conversation history
    messages = await message_service.get_messages_by_session(session_id)

    # Process with agent
    graph = LegalConsultationGraph(db)
    state = AgentState(
        session_id=str(session_id),
        messages=[{"role": m.role, "content": m.content} for m in messages],
        user_message=request.message,
        retrieved_context=[],
        response="",
        intent="",
        sources=[],
        summary=""
    )

    result = await graph.process(state)

    async def generate():
        # Stream the response
        yield f"data: {json.dumps({'type': 'token', 'data': result['response']})}\n\n"
        yield f"data: {json.dumps({'type': 'sources', 'data': result['sources']})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'data': {'session_id': str(session_id)}})}\n\n"

        # Save after streaming
        await message_service.save_exchange(
            session_id,
            request.message,
            result["response"],
            {"sources": result["sources"]}
        )

        if len(messages) == 0:
            await session_service.update_session(
                session_id,
                {"title": request.message[:50] + "..." if len(request.message) > 50 else request.message}
            )
        else:
            await session_service.increment_message_count(session_id)

        log.info("chat_completed",
                session_id=str(session_id),
                message_count=len(messages) + 1)

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Step 3: Test endpoints**

```bash
# Test non-streaming
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is contract law?"}'

# Test streaming
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

**Step 4: Commit**

```bash
cd backend
git add app/api/v1/chat.py app/services/message_service.py
git commit -m "feat: add chat API with streaming support"
```

---

## Phase 6: Frontend - Setup & Core Components

### Task 6.1: Frontend Main Entry

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/index.css`

**Step 1: Create main.tsx**

Create `frontend/src/main.tsx`:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
```

**Step 2: Create App.tsx**

Create `frontend/src/App.tsx`:

```typescript
import { Routes, Route } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import HistoryPage from './pages/HistoryPage';
import AdminPage from './pages/AdminPage';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </div>
  );
}

export default App;
```

**Step 3: Create index.css**

Create `frontend/src/index.css`:

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
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
```

**Step 4: Create placeholder pages**

Create `frontend/src/pages/ChatPage.tsx`:

```typescript
export default function ChatPage() {
  return <div>Chat Page</div>;
}
```

Create `frontend/src/pages/HistoryPage.tsx`:

```typescript
export default function HistoryPage() {
  return <div>History Page</div>;
}
```

Create `frontend/src/pages/AdminPage.tsx`:

```typescript
export default function AdminPage() {
  return <div>Admin Page</div>;
}
```

**Step 5: Verify it runs**

```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

**Step 6: Commit**

```bash
cd frontend
git add src/
git commit -m "feat: add frontend main entry and routing"
```

---

### Task 6.2: API Client

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/types.ts`

**Step 1: Create types**

Create `frontend/src/lib/types.ts`:

```typescript
export interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  summary: string | null;
  message_count: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata: {
    sources?: string[];
  } | null;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  category: string | null;
  source: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  session_id?: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  sources: string[];
}

export interface StreamChunk {
  type: 'token' | 'sources' | 'done' | 'error';
  data: string | string[] | { session_id: string };
}
```

**Step 2: Create API client**

Create `frontend/src/lib/api.ts`:

```typescript
import axios from 'axios';
import type { Session, Message, KnowledgeDocument, ChatRequest, ChatResponse } from './types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Sessions
export const sessionsApi = {
  list: () => api.get<Session[]>('/sessions'),
  get: (id: string) => api.get<Session>(`/sessions/${id}`),
  create: (title?: string) => api.post<Session>('/sessions', { title }),
  update: (id: string, title: string) => api.put<Session>(`/sessions/${id}`, { title }),
  delete: (id: string) => api.delete(`/sessions/${id}`),
};

// Chat
export const chatApi = {
  send: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', request);
    return response.data;
  },

  sendStream: async (request: ChatRequest, onChunk: (chunk: string) => void) => {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) throw new Error('No reader');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'token') {
            onChunk(data.data);
          }
        }
      }
    }
  },
};

// Knowledge
export const knowledgeApi = {
  list: () => api.get<KnowledgeDocument[]>('/knowledge'),
  upload: (file: File, title: string, category?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (category) formData.append('category', category);

    return api.post<KnowledgeDocument>('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete: (id: string) => api.delete(`/knowledge/${id}`),
  search: (q: string, limit = 10) =>
    api.get<{ text: string; score: number; metadata: { title: string; source: string } }[]>(
      `/knowledge/search?q=${encodeURIComponent(q)}&limit=${limit}`
    ),
};

export default api;
```

**Step 3: Commit**

```bash
cd frontend
git add src/lib/
git commit -m "feat: add API client and TypeScript types"
```

---

### Task 6.3: Chat State Management

**Files:**
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/hooks/useSessions.ts`

**Step 1: Create useChat hook**

Create `frontend/src/hooks/useChat.ts`:

```typescript
import { useState, useCallback } from 'react';
import { chatApi } from '@/lib/api';
import type { ChatRequest, Message } from '@/lib/types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();

  const sendMessage = useCallback(async (request: ChatRequest) => {
    setIsLoading(true);
    setCurrentResponse('');
    setSources([]);

    try {
      await chatApi.sendStream(request, (chunk) => {
        setCurrentResponse((prev) => prev + chunk);
      });

      // Add messages to state
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: request.message } as Message,
        { role: 'assistant', content: currentResponse } as Message,
      ]);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentResponse('');
    setSources([]);
  }, []);

  return {
    messages,
    isLoading,
    currentResponse,
    sources,
    sessionId,
    sendMessage,
    clearMessages,
    setSessionId,
  };
}
```

**Step 2: Create useSessions hook**

Create `frontend/src/hooks/useSessions.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionsApi } from '@/lib/api';
import type { Session } from '@/lib/types';

export function useSessions() {
  const queryClient = useQueryClient();

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const response = await sessionsApi.list();
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: (title?: string) => sessionsApi.create(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      sessionsApi.update(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => sessionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  return {
    sessions: sessions || [],
    isLoading,
    createSession: createMutation.mutate,
    updateSession: updateMutation.mutate,
    deleteSession: deleteMutation.mutate,
  };
}
```

**Step 3: Commit**

```bash
cd frontend
git add src/hooks/
git commit -m "feat: add chat and sessions hooks"
```

---

### Task 6.4: Chat View Component

**Files:**
- Create: `frontend/src/components/chat/ChatView.tsx`
- Create: `frontend/src/components/chat/MessageBubble.tsx`
- Create: `frontend/src/components/chat/MessageInput.tsx`
- Create: `frontend/src/components/chat/StreamingText.tsx`

**Step 1: Create MessageBubble component**

Create `frontend/src/components/chat/MessageBubble.tsx`:

```typescript
import type { Message } from '@/lib/types';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const sources = message.metadata?.sources || [];

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {sources.length > 0 && !isUser && (
          <div className="mt-2 pt-2 border-t border-gray-300">
            <p className="text-xs opacity-75">来源:</p>
            <ul className="text-xs opacity-75 list-disc list-inside">
              {sources.map((source, i) => (
                <li key={i}>{source}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Create StreamingText component**

Create `frontend/src/components/chat/StreamingText.tsx`:

```typescript
import { useEffect, useState } from 'react';

interface StreamingTextProps {
  text: string;
  speed?: number;
}

export default function StreamingText({ text, speed = 10 }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    setDisplayedText(text);
  }, [text]);

  return (
    <p className="whitespace-pre-wrap">
      {displayedText}
      {text !== displayedText && <span className="animate-pulse">|</span>}
    </p>
  );
}
```

**Step 3: Create MessageInput component**

Create `frontend/src/components/chat/MessageInput.tsx`:

```typescript
import { useState, FormEvent } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="请输入您的法律问题..."
        disabled={disabled}
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        发送
      </button>
    </form>
  );
}
```

**Step 4: Create ChatView component**

Create `frontend/src/components/chat/ChatView.tsx`:

```typescript
import { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import StreamingText from './StreamingText';
import MessageInput from './MessageInput';
import type { Message } from '@/lib/types';

interface ChatViewProps {
  messages: Message[];
  currentResponse: string;
  isLoading: boolean;
  onSend: (message: string) => void;
}

export default function ChatView({
  messages,
  currentResponse,
  isLoading,
  onSend,
}: ChatViewProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse]);

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && !currentResponse && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>请输入您的法律问题开始咨询</p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {currentResponse && (
          <div className="flex justify-start mb-4">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-white text-gray-800 border border-gray-200">
              <StreamingText text={currentResponse} />
            </div>
          </div>
        )}

        {isLoading && !currentResponse && (
          <div className="flex justify-start mb-4">
            <div className="bg-white rounded-lg px-4 py-2 border border-gray-200">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-4 bg-white">
        <MessageInput onSend={onSend} disabled={isLoading} />
      </div>
    </div>
  );
}
```

**Step 5: Update ChatPage to use ChatView**

Modify `frontend/src/pages/ChatPage.tsx`:

```typescript
import { useState } from 'react';
import ChatView from '@/components/chat/ChatView';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const [input, setInput] = useState('');
  const { messages, currentResponse, isLoading, sendMessage } = useChat();

  const handleSend = (message: string) => {
    sendMessage({ message });
  };

  return (
    <ChatView
      messages={messages}
      currentResponse={currentResponse}
      isLoading={isLoading}
      onSend={handleSend}
    />
  );
}
```

**Step 6: Commit**

```bash
cd frontend
git add src/components/chat/ src/pages/ChatPage.tsx
git commit -m "feat: add ChatView component with streaming support"
```

---

### Task 6.5: Session List Component

**Files:**
- Create: `frontend/src/components/common/SessionList.tsx`
- Create: `frontend/src/components/common/Sidebar.tsx`

**Step 1: Create SessionList component**

Create `frontend/src/components/common/SessionList.tsx`:

```typescript
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { Session } from '@/lib/types';

interface SessionListProps {
  sessions: Session[];
  activeId?: string;
  onSelect: (session: Session) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

export default function SessionList({
  sessions,
  activeId,
  onSelect,
  onRename,
  onDelete,
}: SessionListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const handleStartEdit = (session: Session) => {
    setEditingId(session.id);
    setEditTitle(session.title || '未命名会话');
  };

  const handleSaveEdit = () => {
    if (editingId) {
      onRename(editingId, editTitle);
      setEditingId(null);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      {sessions.length === 0 ? (
        <div className="p-4 text-center text-gray-400">
          <p>暂无会话记录</p>
        </div>
      ) : (
        <ul>
          {sessions.map((session) => (
            <li
              key={session.id}
              className={`border-b border-gray-200 hover:bg-gray-50 ${
                activeId === session.id ? 'bg-blue-50' : ''
              }`}
            >
              {editingId === session.id ? (
                <div className="p-3 flex items-center gap-2">
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="flex-1 px-2 py-1 border rounded"
                    autoFocus
                  />
                  <button onClick={handleSaveEdit} className="text-green-500">
                    保存
                  </button>
                  <button onClick={() => setEditingId(null)} className="text-gray-500">
                    取消
                  </button>
                </div>
              ) : (
                <div
                  className="p-3 cursor-pointer"
                  onClick={() => onSelect(session)}
                  onContextMenu={(e) => {
                    e.preventDefault();
                    handleStartEdit(session);
                  }}
                >
                  <p className="font-medium truncate">
                    {session.title || '未命名会话'}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {session.message_count} 条消息 ·
                    {formatDistanceToNow(new Date(session.updated_at), {
                      addSuffix: true,
                      locale: zhCN,
                    })}
                  </p>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

**Step 2: Create Sidebar component**

Create `frontend/src/components/common/Sidebar.tsx`:

```typescript
import { Link, useLocation } from 'react-router-dom';
import SessionList from './SessionList';
import { useSessions } from '@/hooks/useSessions';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeSessionId?: string;
  onSessionSelect: (id: string) => void;
}

export default function Sidebar({
  isOpen,
  onClose,
  activeSessionId,
  onSessionSelect,
}: SidebarProps) {
  const location = useLocation();
  const { sessions, createSession, deleteSession, updateSession } = useSessions();

  const handleNewChat = () => {
    createSession(undefined, {
      onSuccess: (data) => {
        onSessionSelect(data.data.id);
      },
    });
    if (location.pathname !== '/') {
      onClose();
    }
  };

  return (
    <div
      className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-transform duration-300 ease-in-out`}
    >
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewChat}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            新对话
          </button>
        </div>

        <SessionList
          sessions={sessions}
          activeId={activeSessionId}
          onSelect={(s) => {
            onSessionSelect(s.id);
            onClose();
          }}
          onRename={updateSession}
          onDelete={deleteSession}
        />

        <div className="p-4 border-t border-gray-200">
          <nav className="space-y-2">
            <Link
              to="/history"
              onClick={onClose}
              className="block px-4 py-2 rounded hover:bg-gray-100"
            >
              历史记录
            </Link>
            <Link
              to="/admin"
              onClick={onClose}
              className="block px-4 py-2 rounded hover:bg-gray-100"
            >
              知识库管理
            </Link>
          </nav>
        </div>
      </div>
    </div>
  );
}
```

**Step 3: Update ChatPage with Sidebar**

Modify `frontend/src/pages/ChatPage.tsx`:

```typescript
import { useState } from 'react';
import ChatView from '@/components/chat/ChatView';
import Sidebar from '@/components/common/Sidebar';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { messages, currentResponse, isLoading, sendMessage, setSessionId } = useChat();

  const handleSend = (message: string) => {
    sendMessage({ message });
  };

  return (
    <div className="flex h-screen">
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md hover:bg-gray-50"
      >
        ☰
      </button>

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onSessionSelect={setSessionId}
      />

      <div className="flex-1">
        <ChatView
          messages={messages}
          currentResponse={currentResponse}
          isLoading={isLoading}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}
```

**Step 4: Install date-fns**

```bash
cd frontend
npm install date-fns
```

**Step 5: Commit**

```bash
cd frontend
git add src/components/common/ src/pages/ChatPage.tsx package.json
git commit -m "feat: add sidebar with session list"
```

---

### Task 6.6: History Page

**Files:**
- Modify: `frontend/src/pages/HistoryPage.tsx`

**Step 1: Implement HistoryPage**

Modify `frontend/src/pages/HistoryPage.tsx`:

```typescript
import { useNavigate } from 'react-router-dom';
import { useSessions } from '@/hooks/useSessions';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { sessions, isLoading, deleteSession } = useSessions();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">历史会话</h1>

      {sessions.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          <p>暂无会话记录</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/?session=${session.id}`)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-medium text-lg">
                    {session.title || '未命名会话'}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {session.message_count} 条消息 ·
                    {formatDistanceToNow(new Date(session.updated_at), {
                      addSuffix: true,
                      locale: zhCN,
                    })}
                  </p>
                  {session.summary && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {session.summary}
                    </p>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('确定删除此会话吗？')) {
                      deleteSession(session.id);
                    }
                  }}
                  className="ml-4 px-3 py-1 text-red-500 hover:bg-red-50 rounded"
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
cd frontend
git add src/pages/HistoryPage.tsx
git commit -m "feat: add history page with session list"
```

---

### Task 6.7: Admin Page Components

**Files:**
- Create: `frontend/src/components/admin/DocumentUpload.tsx`
- Create: `frontend/src/components/admin/DocumentList.tsx`
- Create: `frontend/src/components/admin/SearchPreview.tsx`
- Modify: `frontend/src/pages/AdminPage.tsx`
- Create: `frontend/src/hooks/useKnowledge.ts`

**Step 1: Create useKnowledge hook**

Create `frontend/src/hooks/useKnowledge.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeApi } from '@/lib/api';
import type { KnowledgeDocument } from '@/lib/types';

export function useKnowledge() {
  const queryClient = useQueryClient();

  const { data: documents, isLoading } = useQuery({
    queryKey: ['knowledge'],
    queryFn: async () => {
      const response = await knowledgeApi.list();
      return response.data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, title, category }: {
      file: File;
      title: string;
      category?: string;
    }) => knowledgeApi.upload(file, title, category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => knowledgeApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });

  return {
    documents: documents || [],
    isLoading,
    uploadDocument: uploadMutation.mutate,
    deleteDocument: deleteMutation.mutate,
  };
}
```

**Step 2: Create DocumentUpload component**

Create `frontend/src/components/admin/DocumentUpload.tsx`:

```typescript
import { useState, useRef } from 'react';

interface DocumentUploadProps {
  onUpload: (file: File, title: string, category?: string) => void;
  isUploading: boolean;
}

export default function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState<string>('law');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const categories = [
    { value: 'law', label: '法律法规' },
    { value: 'case', label: '典型案例' },
    { value: 'contract', label: '合同模板' },
    { value: 'interpretation', label: '司法解释' },
  ];

  const handleFile = (file: File) => {
    if (file && title) {
      onUpload(file, title, category);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-lg font-semibold mb-4">上传文档</h2>

      <div className="space-y-4">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="文档标题"
          className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {categories.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <p className="text-gray-600">
            {isDragging ? '释放文件以上传' : '点击或拖拽文件到此处上传'}
          </p>
          <p className="text-sm text-gray-400 mt-2">支持 PDF, DOCX, TXT</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={!title || isUploading}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
        >
          {isUploading ? '上传中...' : '上传文档'}
        </button>
      </div>
    </div>
  );
}
```

**Step 3: Create DocumentList component**

Create `frontend/src/components/admin/DocumentList.tsx`:

```typescript
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import type { KnowledgeDocument } from '@/lib/types';

interface DocumentListProps {
  documents: KnowledgeDocument[];
  onDelete: (id: string) => void;
}

const categoryLabels: Record<string, string> = {
  law: '法律法规',
  case: '典型案例',
  contract: '合同模板',
  interpretation: '司法解释',
};

export default function DocumentList({ documents, onDelete }: DocumentListProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">知识库文档 ({documents.length})</h2>

      {documents.length === 0 ? (
        <p className="text-center text-gray-400 py-8">暂无文档</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-4">标题</th>
                <th className="text-left py-2 px-4">分类</th>
                <th className="text-left py-2 px-4">块数</th>
                <th className="text-left py-2 px-4">上传时间</th>
                <th className="text-left py-2 px-4">操作</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-4">{doc.title}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                      {categoryLabels[doc.category || 'law'] || doc.category}
                    </span>
                  </td>
                  <td className="py-3 px-4">{doc.chunk_count}</td>
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {formatDistanceToNow(new Date(doc.created_at), {
                      addSuffix: true,
                      locale: zhCN,
                    })}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => {
                        if (confirm(`确定删除 "${doc.title}" 吗？`)) {
                          onDelete(doc.id);
                        }
                      }}
                      className="text-red-500 hover:text-red-700"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

**Step 4: Create SearchPreview component**

Create `frontend/src/components/admin/SearchPreview.tsx`:

```typescript
import { useState } from 'react';
import { knowledgeApi } from '@/lib/api';

interface SearchResult {
  text: string;
  score: number;
  metadata: {
    title: string;
    source: string;
  };
}

export default function SearchPreview() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setSearching(true);
    try {
      const response = await knowledgeApi.search(query, 5);
      setResults(response.data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mt-6">
      <h2 className="text-lg font-semibold mb-4">搜索预览</h2>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="输入搜索关键词..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={searching || !query.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
        >
          {searching ? '搜索中...' : '搜索'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((result, i) => (
            <div key={i} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-start">
                <span className="font-medium">{result.metadata.title}</span>
                <span className="text-sm text-gray-500">
                  相关度: {(result.score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">{result.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 5: Implement AdminPage**

Modify `frontend/src/pages/AdminPage.tsx`:

```typescript
import DocumentUpload from '@/components/admin/DocumentUpload';
import DocumentList from '@/components/admin/DocumentList';
import SearchPreview from '@/components/admin/SearchPreview';
import { useKnowledge } from '@/hooks/useKnowledge';

export default function AdminPage() {
  const { documents, isLoading, uploadDocument, deleteDocument } = useKnowledge();

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">知识库管理</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <DocumentUpload
            onUpload={uploadDocument}
            isUploading={isLoading}
          />
          <DocumentList
            documents={documents}
            onDelete={deleteDocument}
          />
        </div>

        <div>
          <SearchPreview />
        </div>
      </div>
    </div>
  );
}
```

**Step 6: Commit**

```bash
cd frontend
git add src/components/admin/ src/pages/AdminPage.tsx src/hooks/useKnowledge.ts
git commit -m "feat: add admin page with document upload, list, and search"
```

---

## Phase 7: Integration & Testing

### Task 7.1: Conftest for Tests

**Files:**
- Create: `backend/tests/conftest.py`

**Step 1: Create conftest.py**

Create `backend/tests/conftest.py`:

```python
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from httpx import AsyncClient


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_legal_consultation"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def session(db_session: AsyncSession):
    from app.models.session import Session
    from app.schemas.session import SessionCreate

    session_obj = Session(title="Test Session")
    db_session.add(session_obj)
    await db_session.commit()
    await db_session.refresh(session_obj)
    return session_obj
```

**Step 2: Commit**

```bash
cd backend
git add tests/conftest.py
git commit -m "test: add conftest with test fixtures"
```

---

### Task 7.2: API Integration Tests

**Files:**
- Create: `backend/tests/api/test_sessions_api.py`
- Create: `backend/tests/api/test_chat_api.py`

**Step 1: Write sessions API tests**

Create `backend/tests/api/test_sessions_api.py`:

```python
import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    response = await client.post("/api/v1/sessions", json={"title": "Test Session"})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Session"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sessions(client, session):
    response = await client.get("/api/v1/sessions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_session(client, session):
    response = await client.get(f"/api/v1/sessions/{session.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(session.id)


@pytest.mark.asyncio
async def test_update_session(client, session):
    response = await client.put(f"/api/v1/sessions/{session.id}", json={"title": "Updated"})

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_session(client, session):
    response = await client.delete(f"/api/v1/sessions/{session.id}")

    assert response.status_code == 200

    # Verify deleted
    get_response = await client.get(f"/api/v1/sessions/{session.id}")
    assert get_response.status_code == 404
```

**Step 2: Write chat API tests**

Create `backend/tests/api/test_chat_api.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_chat_creates_session(client):
    with patch('app.agents.orchestrator.LegalConsultationGraph') as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.process.return_value = {
            "response": "Test response",
            "sources": [],
            "messages": []
        }
        mock_graph.return_value = mock_instance

        response = await client.post("/api/v1/chat", json={"message": "Hello"})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["response"] == "Test response"


@pytest.mark.asyncio
async def test_chat_with_session(client, session):
    with patch('app.agents.orchestrator.LegalConsultationGraph') as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.process.return_value = {
            "response": "Test response",
            "sources": ["Test Law"],
            "messages": []
        }
        mock_graph.return_value = mock_instance

        response = await client.post(
            "/api/v1/chat",
            json={"session_id": str(session.id), "message": "Question"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session.id)
```

**Step 3: Run tests**

```bash
cd backend
pytest tests/api/ -v
```

**Step 4: Commit**

```bash
cd backend
git add tests/api/
git commit -m "test: add API integration tests"
```

---

### Task 7.3: End-to-End Test

**Files:**
- Create: `backend/tests/test_e2e.py`

**Step 1: Create E2E test**

Create `backend/tests/test_e2e.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_full_conversation_flow(client):
    """Test complete conversation: create session, chat, list, delete"""

    # Create session
    session_response = await client.post("/api/v1/sessions", json={"title": "Legal Consultation"})
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]

    # Send message
    with patch('app.agents.orchestrator.LegalConsultationGraph') as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.process.return_value = {
            "response": "Based on contract law...",
            "sources": ["Contract Law Section 1"],
            "messages": [],
            "summary": None
        }
        mock_graph.return_value = mock_instance

        chat_response = await client.post(
            "/api/v1/chat",
            json={"session_id": session_id, "message": "What is a contract?"}
        )

        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert chat_data["response"] == "Based on contract law..."
        assert len(chat_data["sources"]) > 0

    # List sessions
    list_response = await client.get("/api/v1/sessions")
    assert list_response.status_code == 200
    sessions = list_response.json()
    assert any(s["id"] == session_id for s in sessions)

    # Delete session
    delete_response = await client.delete(f"/api/v1/sessions/{session_id}")
    assert delete_response.status_code == 200
```

**Step 2: Run E2E test**

```bash
cd backend
pytest tests/test_e2e.py -v
```

**Step 3: Commit**

```bash
cd backend
git add tests/test_e2e.py
git commit -m "test: add end-to-end conversation flow test"
```

---

### Task 7.4: Documentation & Deployment

**Files:**
- Modify: `README.md` (root)
- Create: `docker-compose.yml` (root)
- Create: `.env.example` (root)

**Step 1: Create root README**

Create `README.md`:

```markdown
# 法律咨询助手 (Legal Consultation Assistant)

An AI-powered legal consultation platform providing accessible legal information to the public.

## Features

- Multi-turn legal consultations with context awareness
- RAG-based responses with citations
- Session management with history
- Auto-summary for long conversations
- Knowledge base admin panel
- Streaming responses

## Tech Stack

**Backend:**
- FastAPI + Python
- PostgreSQL
- ChromaDB
- LangChain + LangGraph
- OpenAI GPT-4

**Frontend:**
- React + TypeScript
- TanStack Query
- Axios

## Quick Start

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your OpenAI API key

uv sync
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker (optional)

```bash
docker-compose up -d
```

## Development

See [Backend README](backend/README.md) and [Frontend README](frontend/README.md) for details.
```

**Step 2: Create docker-compose.yml**

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: legal_user
      POSTGRES_PASSWORD: legal_pass
      POSTGRES_DB: legal_consultation
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://legal_user:legal_pass@postgres:5432/legal_consultation
      DATABASE_URL_SYNC: postgresql://legal_user:legal_pass@postgres:5432/legal_consultation
    depends_on:
      - postgres
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Step 3: Create root .env.example**

Create `.env.example`:

```env
# Backend
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/legal_consultation
```

**Step 4: Commit**

```bash
git add README.md docker-compose.yml .env.example
git commit -m "docs: add project README, docker-compose, and env example"
```

---

## Summary

This implementation plan covers:

1. **Project Setup** - Backend/frontend structure, dependencies
2. **Database Models** - Sessions, Messages, KnowledgeDocuments
3. **Core APIs** - CRUD for sessions, messages, knowledge
4. **Knowledge Base** - ChromaDB, embeddings, document processing
5. **LLM Integration** - Intent router, RAG retriever, response generator, summary generator, LangGraph orchestrator
6. **Frontend** - Chat interface, session management, admin panel
7. **Testing** - Unit, integration, E2E tests
8. **Documentation** - README, docker-compose

**Total tasks:** 47 bite-sized tasks following TDD principles.

**Next:** Use `superpowers:executing-plans` or `superpowers:subagent-driven-development` to implement this plan.
