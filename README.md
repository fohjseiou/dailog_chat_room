# 法律咨询助手 (Legal Consultation Assistant)

AI-powered legal consultation platform with RAG-based responses using Alibaba DashScope Qwen and LangChain/LangGraph agents.

## Features

- Multi-turn legal consultation chat
- Context-aware conversations
- Knowledge base with vector search (ChromaDB + DashScope embeddings)
- Session management
- LangChain/LangGraph agent orchestration
- Admin panel for knowledge base management

## Tech Stack

- **Backend:** FastAPI, Python, LangChain, LangGraph
- **LLM:** Alibaba DashScope Qwen (qwen-plus)
- **Embeddings:** DashScope text-embedding-v3
- **Frontend:** React, TypeScript, Vite
- **Database:** SQLite (local), PostgreSQL (production)
- **Vector DB:** ChromaDB
- **Agent Framework:** LangChain + LangGraph

## Quick Start

### Backend

1. Configure environment:
```bash
cd backend
cp .env.example .env
# Edit .env with your DashScope API key
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

See `.env.example` for required variables:

- `DASHSCOPE_API_KEY`: Alibaba DashScope API key (required)
- `DASHSCOPE_MODEL`: Qwen model to use (default: qwen-plus)
- `DASHSCOPE_EMBEDDING_MODEL`: Embedding model (default: text-embedding-v3)

Get API key from: https://dashscope.console.aliyun.com/

## API Documentation

Start the backend and visit http://localhost:8000/docs

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## Architecture

The system uses LangGraph to orchestrate multiple agents:

1. **Intent Router Agent**: Classifies user intent (greeting, legal consultation, general chat)
2. **RAG Retriever Agent**: Searches knowledge base using DashScope embeddings
3. **Response Generator Agent**: Generates responses using Qwen with retrieved context

## Agent Flow

```
User Input → Intent Router → RAG Retriever → Response Generator → Output
                                ↓
                          (periodic)
                    Summary Generator Agent
```

## License

MIT
