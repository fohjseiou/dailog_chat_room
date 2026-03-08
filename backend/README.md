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
