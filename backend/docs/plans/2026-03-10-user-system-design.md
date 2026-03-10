# User Authentication and Multi-User Memory System Design

**Date:** 2026-03-10
**Status:** Approved
**Approach:** Incremental Layer (Approach A)

## Goal

Add user authentication with multi-user session isolation and implement a comprehensive memory system with short-term (cross-session context) and long-term (preferences, facts, summaries) memory extensions.

## Architecture Overview

Add user system as a new layer on top of existing architecture with minimal refactoring. Maintain backward compatibility - anonymous sessions continue to work, while authenticated users get isolated data and enhanced memory features.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Authentication | Simple username + password | Fastest to implement, suitable for demo/development |
| Data migration | Keep existing sessions anonymous (user_id = NULL) | No disruption to existing data |
| Session isolation | Standard multi-user (users see only their own sessions) | Expected behavior for multi-user apps |
| Short-term memory | Cross-session context from last N sessions | Provides continuity across conversations |
| Long-term memory | Hybrid: DB for preferences, ChromaDB for facts/summaries | Best of both - structured + semantic search |

## Components

### 1. Database Schema

#### New Models

**User Model**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
```

**UserPreference Model** (structured long-term memory)
```python
class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="cascade"), nullable=False)
    key = Column(String(100), nullable=False)  # e.g., "response_style", "preferred_length"
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_user_preferences_user_id_key", "user_id", "key"),
    )
```

#### Modified Models

**Session Model** (add user_id)
```python
user_id = Column(String(36), ForeignKey("users.id", ondelete="set null"), nullable=True)
user = relationship("User", back_populates="sessions")
```

**Message Model** (add user_id)
```python
user_id = Column(String(36), ForeignKey("users.id", ondelete="set null"), nullable=True)
```

#### Vector Collections (ChromaDB)

- `user_facts_{user_id}`: Facts about the user extracted from conversations
- `conversation_summaries_{user_id}`: Session summaries for semantic search

### 2. Authentication & API Design

#### New Schemas

```python
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    last_login: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

#### New API Endpoints

```python
# app/api/v1/auth.py
POST /auth/register     - Register new user
POST /auth/login        - Login and receive JWT token
GET  /auth/me           - Get current user info
```

#### Authentication Flow

- Password hashing: `passlib` with bcrypt
- JWT tokens: 7-day expiration, signed with secret key
- Token format: `Authorization: Bearer <token>`
- Optional auth: Requests without token are treated as anonymous

### 3. Memory Service Design

```python
class MemoryService:
    async def get_short_term_context(user_id: str, limit: int = 3) -> List[Dict]:
        """Get recent conversation context from last N sessions."""

    async def get_long_term_memory(user_id: str, query: str, top_k: int = 5) -> Dict:
        """Retrieve relevant long-term memories (facts + summaries)."""

    async def save_user_fact(user_id: str, fact: str, metadata: Dict) -> None:
        """Extract and store a fact about the user."""

    async def save_conversation_summary(user_id: str, session_id: str, summary: str) -> None:
        """Store conversation summary in vector store."""

    async def get_preferences(user_id: str) -> Dict[str, str]:
        """Get structured user preferences from DB."""

    async def set_preference(user_id: str, key: str, value: str) -> None:
        """Store or update a user preference."""
```

#### Integration with Chat Flow

The `response_generator_node` will be enhanced to:
1. Check if user_id exists in AgentState
2. Retrieve short-term context (last N sessions)
3. Retrieve long-term memory (facts + summaries) via semantic search
4. Retrieve user preferences from DB
5. Enhance system prompt with all memory sources

### 4. Modified Session & Chat APIs

#### Session Service Updates

```python
async def create_session(data, user_id: Optional[str] = None) -> SessionResponse:
    """Pass user_id when creating session."""

async def list_sessions(user_id: Optional[str] = None) -> List[SessionResponse]:
    """Filter by user_id if provided, otherwise return all (anonymous)."""
```

#### API Endpoint Updates

```python
@router.post("")
async def create_session(
    data: Optional[SessionCreate] = Body(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create session - associates with logged-in user if available."""
    user_id = current_user.id if current_user else None
    return await service.create_session(data, user_id=user_id)

@router.get("")
async def list_sessions(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List sessions - only show user's own sessions if logged in."""
    user_id = current_user.id if current_user else None
    return await service.list_sessions(user_id=user_id)
```

#### Agent State Updates

```python
class AgentState(TypedDict):
    user_message: str
    user_id: Optional[str]  # NEW: Track user for memory
    conversation_history: List[Dict[str, str]]
    user_intent: str
    retrieved_context: Optional[List[Dict[str, Any]]]
    context_str: Optional[str]
    sources: Optional[List[Dict[str, Any]]]
    response: Optional[str]
    error: Optional[str]
```

### 5. Frontend Integration

#### New API Client Methods

```typescript
export const authAPI = {
  register: (username: string, password: string) => api.post<UserResponse>('/auth/register', { username, password }),
  login: (username: string, password: string) => api.post<TokenResponse>('/auth/login', { username, password }),
  getCurrentUser: () => api.get<UserResponse>('/auth/me'),
};
```

#### Auth State Management

```typescript
interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, password: string) => Promise<void>;
}
```

#### UI Components

- `LoginForm.tsx` - Login/registration form
- `UserMenu.tsx` - User dropdown menu (shows when logged in)
- Token interceptor - Adds `Authorization: Bearer <token>` to all API requests

### 6. Error Handling & Edge Cases

#### Auth Errors

| Scenario | Handling |
|----------|----------|
| Duplicate username | 400 "Username already exists" |
| Wrong password | 401 "Invalid credentials" |
| Expired token | 401, prompt re-login |
| Invalid token | 401, treat as anonymous |

#### Session Ownership

- Users can only access their own sessions (403 if trying to access others')
- Anonymous sessions can be "claimed" after login via optional `/sessions/{id}/claim` endpoint

#### Memory Edge Cases

| Scenario | Handling |
|----------|----------|
| New user (no memories) | Return empty context, no errors |
| Vector store unavailable | Fall back to DB-only (preferences only) |
| Memory extraction fails | Log error, continue without memory |
| ChromaDB timeout | Use cached result if available, else skip |

### 7. Testing Strategy

#### Unit Tests

- `test_auth_service.py` - Registration, login, password hashing
- `test_memory_service.py` - Short-term context, long-term memory, preferences
- `test_session_service_isolation.py` - Multi-user isolation, anonymous support

#### Integration Tests

- `test_user_workflow.py` - Registration, login, authenticated chat
- `test_multi_user_session_isolation.py` - Users can't see each other's data
- `test_memory_integration.py` - Memory-enhanced responses, fact extraction

#### E2E Frontend Tests

- `LoginForm.test.tsx` - Form validation, submit behavior, error handling
- `UserMenu.test.tsx` - Display, logout functionality

### 8. Configuration & Migration

#### Config Updates

```python
class Settings(BaseSettings):
    # Auth
    secret_key: str
    password_min_length: int = 6
    jwt_expire_days: int = 7

    # Memory
    short_term_session_limit: int = 3
    long_term_memory_top_k: int = 5
    enable_memory_extraction: bool = True
```

#### Database Migration

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE user_preferences (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value VARCHAR(500) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);

ALTER TABLE sessions ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE messages ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX ix_sessions_user_id ON sessions(user_id);
CREATE INDEX ix_messages_user_id ON messages(user_id);
```

## Implementation Order

1. Database models and migration
2. Authentication service (hashing, JWT)
3. Auth API endpoints (/register, /login, /me)
4. Session service updates (user_id filtering)
5. Memory service implementation
6. Agent state and node updates for memory integration
7. Frontend auth store and components
8. API client updates with token handling
9. Testing and verification

## Success Criteria

- [ ] Users can register and login
- [ ] Authenticated users only see their own sessions
- [ ] Anonymous sessions still work (backward compatible)
- [ ] Short-term memory includes context from last 3 sessions
- [ ] Long-term memory retrieves relevant facts and summaries
- [ ] User preferences persist and influence responses
- [ ] All tests pass (unit, integration, E2E)
- [ ] No breaking changes to existing frontend

## Next Steps

This design document will be used to create a detailed implementation plan using the `writing-plans` skill.
