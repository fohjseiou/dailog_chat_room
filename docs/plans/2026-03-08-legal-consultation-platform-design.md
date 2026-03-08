# Legal Consultation Platform - Design Document

**Date:** 2026-03-08
**Status:** Approved
**Author:** Design Team

## 1. Overview

### 1.1 Project Goals

Build an AI-powered legal consultation platform that provides accessible, preliminary legal information to the general public.

**Target Users:** General public seeking preliminary legal guidance

**Core Value:** Affordable, accessible legal information reference (not legal advice)

### 1.2 Scope

**In Scope:**
- Text-based chat interface
- Multi-turn conversations with context memory
- Session management (create, rename, delete, history)
- Auto-summary generation for long conversations
- Vector knowledge base (laws, cases, contracts, interpretations)
- Admin panel for knowledge base CRUD
- RAG-based response generation with citations

**Out of Scope (Future):**
- Voice/video input
- User authentication
- Payment integration
- Lawyer matching
- Formal legal opinion generation

## 2. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Frontend | React + TypeScript | Industry standard, strong ecosystem |
| Backend | FastAPI + Python | Native support for LangChain/LangGraph, async performance |
| Database | PostgreSQL | Reliable, relational data for sessions/messages |
| Vector DB | ChromaDB | Open-source, local-friendly, easy setup |
| LLM | OpenAI GPT-4/o1 | Best quality for complex reasoning |
| Embeddings | OpenAI text-embedding-3-small | Cost-effective, high quality |
| Agent Framework | LangChain + LangGraph | Sophisticated agent orchestration |
| Deployment | Local first, cloud later | Flexibility for iteration |

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React + TypeScript)           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Chat View    │  │ History List │  │ Admin Knowledge Panel│  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST + WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Chat API     │  │ Session API  │  │ Knowledge API        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                              │                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           LangGraph Agent Orchestrator                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐   │   │
│  │  │Intent   │ │RAG      │ │Response │ │Summary       │   │   │
│  │  │Router   │ │Retriever│ │Generator│ │Generator     │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌───────────┐  ┌───────────┐  ┌─────────────┐
        │PostgreSQL │  │ ChromaDB  │  │   OpenAI    │
        │ (Sessions)│  │(Vectors)  │  │   (LLM)     │
        └───────────┘  └───────────┘  └─────────────┘
```

### 3.1 Architecture Pattern

**Monolithic with Modular Agents**

- Single FastAPI application
- Modular LangGraph agents for different legal domains
- Internal modularity enables future microservice extraction
- Simpler deployment and debugging for MVP

## 4. Core Components

### 4.1 Chat Engine

- **Message Processing:** Receives user input, routes to appropriate agent
- **Context Window Management:** Maintains conversation history within token limits
- **Response Streaming:** Server-Sent Events (SSE) for real-time output

### 4.2 Session Manager

- **Session Creation:** Auto-create new sessions on first message
- **Context Retrieval:** Fetch conversation history for continuity
- **CRUD Operations:** List, rename, delete sessions
- **Auto-save:** Persist messages after each exchange

### 4.3 Knowledge Retriever (RAG)

- **Embedding Generation:** Convert query to vector using OpenAI embeddings
- **Semantic Search:** Query ChromaDB for top-k similar documents
- **Context Assembly:** Format retrieved docs into prompt context
- **Citation Tracking:** Track source documents for transparency

### 4.4 Summary Generator

- **Trigger:** Auto-generate after N messages or token threshold
- **Content:** Key questions, advice given, action items
- **Storage:** Cached summary for context window optimization

### 4.5 Knowledge Manager (Admin)

- **Document Upload:** Support PDF, DOCX, TXT files
- **Chunking Strategy:** Intelligent document splitting for embedding
- **CRUD Operations:** Add, update, delete documents
- **Batch Operations:** Bulk import/export functionality

## 5. Data Models

### 5.1 PostgreSQL Schema

```sql
-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    summary TEXT,
    message_count INT DEFAULT 0
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB  -- Citations, sources, etc.
);

-- Knowledge Documents
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- 'law' | 'case' | 'contract' | 'interpretation'
    source VARCHAR(500),
    chunk_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 ChromaDB Collection

```
Collection: legal_knowledge
- embedding: OpenAI text-embedding-3-small (1536 dims)
- metadata: { document_id, category, title, chunk_index, source }
- documents: text content
```

### 5.3 Session Context (LangGraph State)

```python
{
    "session_id": str,
    "messages": [{"role": str, "content": str}],
    "retrieved_context": [{"text": str, "source": str, "score": float}],
    "summary": str | None,
    "user_intent": str,
    "awaiting_clarification": bool
}
```

## 6. API Design

### 6.1 Chat APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message, stream response (SSE) |
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/sessions/:id` | Get session with messages |
| PUT | `/api/v1/sessions/:id` | Rename session |
| DELETE | `/api/v1/sessions/:id` | Delete session |
| POST | `/api/v1/sessions/:id/summary` | Trigger manual summary |

### 6.2 Knowledge APIs (Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/knowledge` | List all documents |
| POST | `/api/v1/knowledge/upload` | Upload and embed document |
| DELETE | `/api/v1/knowledge/:id` | Delete document |
| GET | `/api/v1/knowledge/search` | Test semantic search |
| POST | `/api/v1/knowledge/batch` | Bulk import documents |

### 6.3 WebSocket (Alternative)

```
WS /api/v1/ws/chat
- Message: { action: "message", session_id, content }
- Stream: { type: "token"|"error"|"done", data }
```

## 7. LLM Integration

### 7.1 Agent Flow

```
Input → Intent Router → RAG Retriever → Response Generator → Output
                                          ↓
                                    Summary Generator (periodic)
```

### 7.2 Intent Router

Classifies queries into:
- **Legal Consultation:** Requires RAG retrieval
- **General Greeting:** Direct response
- **Clarification Needed:** Ask follow-up
- **Summary Request:** Generate summary

### 7.3 RAG Retrieval Chain

1. Query rewriting/clarification
2. Embedding generation (OpenAI)
3. ChromaDB search (top-k=5-10)
4. Re-ranking by relevance
5. Context assembly with citations

### 7.4 Response System Prompt

```
你是一个专业的法律咨询助手，为普通公众提供初步的法律信息参考。

重要原则：
1. 仅提供法律信息参考，不构成正式法律意见
2. 建议用户在重大事项上咨询专业律师
3. 基于提供的法律知识库回答，引用相关法规
4. 回答要清晰、易懂，避免过度专业术语

参考信息：
{retrieved_context}
```

### 7.5 Summary Trigger

- Message count > 10
- Token usage approaches threshold
- User explicitly requests

## 8. Frontend Design

### 8.1 Page Structure

```
/src
  /pages
    - ChatPage.tsx        # Main chat interface
    - HistoryPage.tsx     # Session history list
    - AdminPage.tsx       # Knowledge base management
  /components
    /chat
      - ChatView.tsx      # Message display area
      - MessageInput.tsx  # Input box with send button
      - MessageBubble.tsx # Individual message component
    /common
      - SessionList.tsx   # Sidebar session list
      - Sidebar.tsx       # Navigation sidebar
      - StreamingText.tsx # Typewriter effect for streaming
    /admin
      - DocumentUpload.tsx # File upload with drag-drop
      - DocumentList.tsx   # Knowledge documents table
      - SearchPreview.tsx  # Test semantic search
  /hooks
    - useChat.ts          # Chat state & streaming logic
    - useSessions.ts      # Session CRUD operations
    - useKnowledge.ts     # Knowledge API calls
```

### 8.2 Key UI Components

**Chat View:**
- Message bubbles with role indicators
- Streaming text with typewriter effect
- Citation badges showing source documents
- Auto-scroll to latest message

**Session Sidebar:**
- Collapsible with session list
- Click to load, right-click for actions
- "New Chat" button at top

**Admin Panel:**
- Drag-drop file upload
- Document table with search/filter
- Category badges
- Bulk actions

## 9. Error Handling

### 9.1 LLM Errors

| Error | Strategy |
|-------|----------|
| Rate Limiting | Exponential backoff, show "busy" |
| Timeout | Return partial + retry option |
| Hallucination | Citation requirements, detect low-confidence |
| No Relevant Docs | Graceful message, suggest broader query |

### 9.2 Knowledge Errors

| Error | Strategy |
|-------|----------|
| Empty Search | Inform user, suggest different terms |
| Embedding Failure | Queue for retry, log error |
| Corrupted Document | Skip chunk, flag for admin |
| Duplicate Upload | Warn, offer replace/skip |

### 9.3 Monitoring

```python
# Metrics
- Response time (p50, p95, p99)
- Token usage per session
- RAG retrieval success rate
- Error rates by type

# Logging
log.info("chat_request",
    session_id=session_id,
    message_length=len(message),
    intent_detected=intent,
    docs_retrieved=len(docs))
```

## 10. Testing Strategy

### 10.1 Test Types

- **Unit Tests:** Intent router, RAG logic, session CRUD
- **Integration Tests:** End-to-end chat, knowledge pipeline
- **LLM Eval:** Retrieval precision, answer relevance, citation accuracy

### 10.2 Manual Checklist

- [ ] Create new session, send message
- [ ] Load existing session, continue conversation
- [ ] Rename and delete sessions
- [ ] Upload document, verify embeddings
- [ ] Search knowledge base
- [ ] Stream response, verify display
- [ ] Test citation links
- [ ] Verify auto-summary generation
- [ ] Test error handling

## 11. Success Criteria

1. Users can have multi-turn legal consultations with context awareness
2. Responses are grounded in the provided knowledge base with citations
3. Admin can easily upload and manage legal documents
4. Long conversations are automatically summarized
5. Platform handles common legal queries accurately
6. System is responsive (streaming responses)

## 12. Next Steps

This design is approved. Proceed to implementation planning via `writing-plans` skill.
