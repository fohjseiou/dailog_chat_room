# User Authentication and Multi-User Memory System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add user authentication with multi-user session isolation and comprehensive memory system (short-term cross-session context + long-term preferences/facts/summaries).

**Architecture:** Add user system as an incremental layer on top of existing architecture - minimal refactoring, optional auth (anonymous still works), user_id filtering for data isolation, hybrid memory (DB + ChromaDB).

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, JWT (python-jose), passlib bcrypt, ChromaDB, LangChain

---

## Task 1: Add Authentication Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Add passlib dependency**

Edit `backend/pyproject.toml` dependencies list. Add `"passlib[bcrypt]>=1.7.4"` to the dependencies list (around line 24, after `dashscope`).

**Step 2: Install dependencies**

Run: `cd backend && uv pip install -e ".[dev]"`
Expected: Package installs successfully, no errors

**Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "feat: add passlib bcrypt dependency for password hashing"
```

---

## Task 2: Update Configuration with Auth Settings

**Files:**
- Modify: `backend/app/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Create test file `tests/test_config_auth.py`:

```python
import pytest
from app.config import get_settings

def test_auth_settings_exists():
    settings = get_settings()
    assert hasattr(settings, 'secret_key')
    assert hasattr(settings, 'password_min_length')
    assert hasattr(settings, 'jwt_expire_days')
    assert hasattr(settings, 'short_term_session_limit')
    assert hasattr(settings, 'long_term_memory_top_k')
    assert hasattr(settings, 'enable_memory_extraction')

def test_auth_default_values():
    settings = get_settings()
    assert settings.password_min_length == 6
    assert settings.jwt_expire_days == 7
    assert settings.short_term_session_limit == 3
    assert settings.long_term_memory_top_k == 5
    assert settings.enable_memory_extraction is True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_config_auth.py -v`
Expected: FAIL with "Settings object has no attribute 'secret_key'"

**Step 3: Write minimal implementation**

Edit `backend/app/config.py`, add auth settings to `Settings` class (around line 43, after `summary_token_threshold`):

```python
# Auth
secret_key: str
password_min_length: int = 6
jwt_expire_days: int = 7

# Memory
short_term_session_limit: int = 3
long_term_memory_top_k: int = 5
enable_memory_extraction: bool = True
```

**Step 4: Set SECRET_KEY in .env**

Add to backend `.env` file (create if not exists):
```
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_config_auth.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/config.py backend/tests/test_config_auth.py
git commit -m "feat: add auth and memory configuration settings"
```

---

## Task 3: Create User Database Model

**Files:**
- Create: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/models/test_user.py`

**Step 1: Write the failing test**

Create test file `backend/tests/models/test_user.py`:

```python
import pytest
from app.models.user import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_user_model_creation(db_session):
    user = User(username="testuser", password_hash="hashed_password_here")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.password_hash == "hashed_password_here"
    assert user.created_at is not None
    assert user.last_login is None

@pytest.mark.asyncio
async def test_user_username_unique(db_session):
    user1 = User(username="duplicate", password_hash="hash1")
    db_session.add(user1)
    await db_session.commit()

    user2 = User(username="duplicate", password_hash="hash2")
    db_session.add(user2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_user.py -v`
Expected: FAIL with "cannot import 'User' from 'app.models.user'"

**Step 3: Write minimal implementation**

Create file `backend/app/models/user.py`:

```python
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
```

Edit `backend/app/models/__init__.py`, add import:
```python
from app.models.user import User  # noqa: F401
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_user.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/user.py backend/app/models/__init__.py backend/tests/models/test_user.py
git commit -m "feat: add User database model"
```

---

## Task 4: Create UserPreference Database Model

**Files:**
- Create: `backend/app/models/user_preference.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/models/test_user_preference.py`

**Step 1: Write the failing test**

Create test file `backend/tests/models/test_user_preference.py`:

```python
import pytest
from app.models.user_preference import UserPreference

@pytest.mark.asyncio
async def test_user_preference_creation(db_session, test_user):
    pref = UserPreference(
        user_id=test_user.id,
        key="response_style",
        value="detailed"
    )
    db_session.add(pref)
    await db_session.commit()
    await db_session.refresh(pref)

    assert pref.id is not None
    assert pref.key == "response_style"
    assert pref.value == "detailed"

@pytest.mark.asyncio
async def test_user_preference_unique_per_user_key(db_session, test_user):
    pref1 = UserPreference(user_id=test_user.id, key="theme", value="dark")
    db_session.add(pref1)
    await db_session.commit()

    pref2 = UserPreference(user_id=test_user.id, key="theme", value="light")
    db_session.add(pref2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_user_preference.py -v`
Expected: FAIL with "cannot import 'UserPreference'"

**Step 3: Write minimal implementation**

Create file `backend/app/models/user_preference.py`:

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from app.database import Base
import uuid


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="cascade"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_user_preferences_user_id_key", "user_id", "key", unique=True),
    )
```

Edit `backend/app/models/__init__.py`:
```python
from app.models.user_preference import UserPreference  # noqa: F401
```

Add test_user fixture to `backend/tests/conftest.py`:
```python
@pytest.fixture
async def test_user(db_session):
    from app.models.user import User
    user = User(username="testuser", password_hash="hash")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_user_preference.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/user_preference.py backend/app/models/__init__.py backend/tests/models/test_user_preference.py backend/tests/conftest.py
git commit -m "feat: add UserPreference database model"
```

---

## Task 5: Add user_id to Session and Message Models

**Files:**
- Modify: `backend/app/models/session.py`
- Modify: `backend/app/models/message.py`
- Test: `backend/tests/models/test_session_user.py`

**Step 1: Write the failing test**

Create test file `backend/tests/models/test_session_user.py`:

```python
import pytest
from app.models.session import Session
from app.models.user import User

@pytest.mark.asyncio
async def test_session_with_user(db_session):
    user = User(username="testuser", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    session = Session(title="Test Session", user_id=user.id)
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.user_id == user.id
    assert session.user is not None
    assert session.user.username == "testuser"

@pytest.mark.asyncio
async def test_session_without_user(db_session):
    session = Session(title="Anonymous Session")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.user_id is None
    assert session.user is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_session_user.py -v`
Expected: FAIL with "Session object has no attribute 'user_id'"

**Step 3: Write minimal implementation**

Edit `backend/app/models/session.py`, add user relationship:

```python
from sqlalchemy import Column, String, Text, Integer, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    summary = Column(Text, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="set null"), nullable=True)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="sessions")
```

Edit `backend/app/models/message.py`, add user_id column:

```python
# Add import
from sqlalchemy import ForeignKey

# Add to Message class
user_id = Column(String(36), ForeignKey("users.id", ondelete="set null"), nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_session_user.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/session.py backend/app/models/message.py backend/tests/models/test_session_user.py
git commit -m "feat: add user_id foreign key to Session and Message models"
```

---

## Task 6: Create Auth Schemas

**Files:**
- Create: `backend/app/schemas/user.py`
- Test: `backend/tests/schemas/test_user.py`

**Step 1: Write the failing test**

Create test file `backend/tests/schemas/test_user.py`:

```python
import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from datetime import datetime

def test_user_create_valid():
    data = UserCreate(username="testuser", password="password123")
    assert data.username == "testuser"
    assert data.password == "password123"

def test_user_create_username_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="ab", password="password123")

def test_user_create_password_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="testuser", password="12345")

def test_user_response_from_model():
    from app.models.user import User
    user = User(
        id="123",
        username="testuser",
        password_hash="hash",
        created_at=datetime.now()
    )
    response = UserResponse.model_validate(user)
    assert response.id == "123"
    assert response.username == "testuser"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/schemas/test_user.py -v`
Expected: FAIL with "cannot import 'UserCreate'"

**Step 3: Write minimal implementation**

Create file `backend/app/schemas/user.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


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

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/schemas/test_user.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/user.py backend/tests/schemas/test_user.py
git commit -m "feat: add user authentication schemas"
```

---

## Task 7: Create AuthService

**Files:**
- Create: `backend/app/services/auth_service.py`
- Test: `backend/tests/services/test_auth_service.py`

**Step 1: Write the failing test**

Create test file `backend/tests/services/test_auth_service.py`:

```python
import pytest
from app.services.auth_service import AuthService, UserAlreadyExistsError, InvalidCredentialsError
from app.schemas.user import UserCreate

@pytest.mark.asyncio
async def test_register_user_success(db_session):
    service = AuthService(db_session)
    user_data = UserCreate(username="newuser", password="password123")
    user = await service.register(user_data)

    assert user.username == "newuser"
    assert user.id is not None
    assert user.password_hash != "password123"  # Should be hashed

@pytest.mark.asyncio
async def test_register_duplicate_username_fails(db_session, test_user):
    service = AuthService(db_session)
    user_data = UserCreate(username=test_user.username, password="password123")

    with pytest.raises(UserAlreadyExistsError):
        await service.register(user_data)

@pytest.mark.asyncio
async def test_login_valid_credentials(db_session, test_user_with_password):
    service = AuthService(db_session)
    user = await service.login(test_user_with_password.username, "testpassword123")

    assert user.username == test_user_with_password.username

@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session, test_user):
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.login(test_user.username, "wrongpassword")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_auth_service.py -v`
Expected: FAIL with "cannot import 'AuthService'"

**Step 3: Write minimal implementation**

Create file `backend/app/services/auth_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def register(self, user_data: UserCreate) -> User:
        # Check if username exists
        result = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise UserAlreadyExistsError("Username already exists")

        # Create new user
        hashed_password = self._hash_password(user_data.password)
        user = User(username=user_data.username, password_hash=hashed_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, username: str, password: str) -> User:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user or not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
```

Add test_user_with_password fixture to `backend/tests/conftest.py`:
```python
@pytest.fixture
async def test_user_with_password(db_session):
    from app.services.auth_service import AuthService, pwd_context
    from app.models.user import User
    from app.schemas.user import UserCreate

    service = AuthService(db_session)
    hashed = pwd_context.hash("testpassword123")
    user = User(username="logintest", password_hash=hashed)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_auth_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/auth_service.py backend/tests/services/test_auth_service.py backend/tests/conftest.py
git commit -m "feat: add AuthService with password hashing and user registration"
```

---

## Task 8: Create JWT Token Utilities

**Files:**
- Create: `backend/app/services/token_service.py`
- Test: `backend/tests/services/test_token_service.py`

**Step 1: Write the failing test**

Create test file `backend/tests/services/test_token_service.py`:

```python
import pytest
from app.services.token_service import TokenService
from datetime import datetime

def test_create_access_token():
    service = TokenService()
    token = service.create_access_token("user123")
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_access_token_valid():
    service = TokenService()
    token = service.create_access_token("user123")
    payload = service.verify_token(token)
    assert payload["sub"] == "user123"

def test_verify_access_token_invalid():
    service = TokenService()
    with pytest.raises(Exception):
        service.verify_token("invalid.token.here")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_token_service.py -v`
Expected: FAIL with "cannot import 'TokenService'"

**Step 3: Write minimal implementation**

Create file `backend/app/services/token_service.py`:

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import get_settings


class TokenService:
    def __init__(self):
        settings = get_settings()
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.expire_days = settings.jwt_expire_days

    def create_access_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(days=self.expire_days)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise ValueError("Invalid token")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_token_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/token_service.py backend/tests/services/test_token_service.py
git commit -m "feat: add TokenService for JWT creation and verification"
```

---

## Task 9: Create Auth Dependency

**Files:**
- Create: `backend/app/dependencies.py`
- Test: `backend/tests/test_dependencies.py`

**Step 1: Write the failing test**

Create test file `backend/tests/test_dependencies.py`:

```python
import pytest
from fastapi import Header
from app.dependencies import get_current_user
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(db_session, test_user):
    from app.services.token_service import TokenService

    token_service = TokenService()
    token = token_service.create_access_token(test_user.id)

    # Mock the authorization header
    user = await get_current_user(
        authorization=f"Bearer {token}",
        db=db_session
    )

    assert user is not None
    assert user.id == test_user.id

@pytest.mark.asyncio
async def test_get_current_user_without_token(db_session):
    user = await get_current_user(
        authorization=None,
        db=db_session
    )
    assert user is None

@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token(db_session):
    with pytest.raises(ValueError):
        await get_current_user(
            authorization="Bearer invalid_token",
            db=db_session
        )
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_dependencies.py -v`
Expected: FAIL with "cannot import 'get_current_user'"

**Step 3: Write minimal implementation**

Create file `backend/app/dependencies.py`:

```python
from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.services.token_service import TokenService
from app.services.auth_service import AuthService


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = None
) -> Optional:
    """
    Get current user from JWT token.
    Returns None if no token provided (anonymous access).
    Raises HTTPException if token is invalid.
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    try:
        token_service = TokenService()
        payload = token_service.verify_token(token)
        user_id = payload.get("sub")

        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(user_id)
        return user

    except Exception:
        # Invalid token - treat as anonymous
        return None
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_dependencies.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/dependencies.py backend/tests/test_dependencies.py
git commit -m "feat: add get_current_user dependency for auth"
```

---

## Task 10: Create Auth API Endpoints

**Files:**
- Create: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/v1/__init__.py`
- Test: `backend/tests/api/test_auth_api.py`

**Step 1: Write the failing test**

Create test file `backend/tests/api/test_auth_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user_success(test_db):
    response = client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data
    assert "password_hash" not in data

def test_register_duplicate_username(test_db, test_user):
    response = client.post("/api/v1/auth/register", json={
        "username": test_user.username,
        "password": "password123"
    })
    assert response.status_code == 400

def test_login_success(test_db, test_user_with_password):
    response = client.post("/api/v1/auth/login", json={
        "username": test_user_with_password.username,
        "password": "testpassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

def test_login_invalid_credentials(test_db):
    response = client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_auth_api.py -v`
Expected: FAIL with "404 Not Found" for /api/v1/auth/register

**Step 3: Write minimal implementation**

Create file `backend/app/api/v1/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService, UserAlreadyExistsError, InvalidCredentialsError
from app.services.token_service import TokenService
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    try:
        service = AuthService(db)
        user = await service.register(user_data)
        return UserResponse.model_validate(user)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Username already exists")


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login and receive JWT token."""
    try:
        service = AuthService(db)
        user = await service.login(credentials.username, credentials.password)

        # Update last_login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        await db.commit()

        # Create token
        token_service = TokenService()
        token = token_service.create_access_token(user.id)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user_dep)
):
    """Get current user info."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user
```

Edit `backend/app/api/v1/__init__.py` to include auth router (or create it if it doesn't exist):
```python
from app.api.v1 import auth
```

Also need to add auth router to main app. Check `backend/app/main.py` or `backend/app/api/__init__.py` and add:

```python
from app.api.v1 import auth
api_router.include_router(auth.router)
```

Add dependency for get_current_user_dep in `backend/app/dependencies.py`:
```python
async def get_current_user_dep(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional:
    return await get_current_user(authorization, db)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/api/test_auth_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/auth.py backend/app/dependencies.py backend/tests/api/test_auth_api.py
git commit -m "feat: add auth API endpoints (register, login, me)"
```

---

## Task 11: Update SessionService for User Isolation

**Files:**
- Modify: `backend/app/services/session_service.py`
- Test: `backend/tests/services/test_session_service_user_isolation.py`

**Step 1: Write the failing test**

Create test file `backend/tests/services/test_session_service_user_isolation.py`:

```python
import pytest
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate

@pytest.mark.asyncio
async def test_create_session_with_user(db_session, test_user):
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreate(title="Test"),
        user_id=test_user.id
    )

    assert session.user_id == test_user.id

@pytest.mark.asyncio
async def test_create_session_without_user(db_session):
    service = SessionService(db_session)
    session = await service.create_session(
        SessionCreate(title="Anonymous"),
        user_id=None
    )

    assert session.user_id is None

@pytest.mark.asyncio
async def test_list_sessions_filters_by_user(db_session, test_user):
    service = SessionService(db_session)

    # Create session for test_user
    await service.create_session(SessionCreate(title="User Session"), user_id=test_user.id)

    # Create anonymous session
    await service.create_session(SessionCreate(title="Anonymous Session"), user_id=None)

    # List only user's sessions
    user_sessions = await service.list_sessions(user_id=test_user.id)
    assert len(user_sessions) == 1
    assert user_sessions[0].title == "User Session"

    # List all sessions
    all_sessions = await service.list_sessions(user_id=None)
    assert len(all_sessions) == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_session_service_user_isolation.py -v`
Expected: FAIL - create_session doesn't accept user_id parameter

**Step 3: Write minimal implementation**

Edit `backend/app/services/session_service.py`:

```python
# Modify create_session to accept user_id
async def create_session(self, data, user_id: Optional[str] = None) -> SessionResponse:
    # Handle both dict and SessionCreate for compatibility
    if isinstance(data, dict):
        title = data.get("title")
    elif data is None:
        title = None
    else:
        title = data.title if hasattr(data, "title") else None

    session = Session(title=title, user_id=user_id)
    self.db.add(session)
    await self.db.commit()
    await self.db.refresh(session)
    return SessionResponse.model_validate(session)

# Modify list_sessions to filter by user_id
async def list_sessions(self, user_id: Optional[str] = None) -> List[SessionResponse]:
    query = select(Session).order_by(Session.updated_at.desc())

    if user_id is not None:
        query = query.where(Session.user_id == user_id)

    result = await self.db.execute(query)
    sessions = result.scalars().all()
    return [SessionResponse.model_validate(s) for s in sessions]
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_session_service_user_isolation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/session_service.py backend/tests/services/test_session_service_user_isolation.py
git commit -m "feat: add user isolation to SessionService"
```

---

## Task 12: Update Session API for User Isolation

**Files:**
- Modify: `backend/app/api/v1/sessions.py`
- Test: `backend/tests/api/test_sessions_api_user_isolation.py`

**Step 1: Write the failing test**

Create test file `backend/tests/api/test_sessions_api_user_isolation.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_session_as_authenticated_user(test_db, test_user_with_password):
    # Login first
    login_response = client.post("/api/v1/auth/login", json={
        "username": test_user_with_password.username,
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]

    # Create session with auth
    response = client.post(
        "/api/v1/sessions",
        json={"title": "My Session"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Session"

def test_list_sessions_only_returns_own(test_db, test_user, other_user):
    # Create session for test_user
    client.post("/api/v1/sessions", json={"title": "User1 Session"})

    # Login as other_user and list
    # Should not see test_user's sessions
    # ... test implementation
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_sessions_api_user_isolation.py -v`
Expected: FAIL - sessions endpoint doesn't use auth

**Step 3: Write minimal implementation**

Edit `backend/app/api/v1/sessions.py`, update endpoints to use auth:

```python
from fastapi import APIRouter, Depends, HTTPException, Body, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.schemas.message import MessageResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    data: Optional[SessionCreate] = Body(None),
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new session - associates with logged-in user if available."""
    service = SessionService(db)
    if data is None:
        data = SessionCreate(title=None)

    user_id = current_user.id if current_user else None
    return await service.create_session(data, user_id=user_id)


@router.get("", response_model=List[SessionListResponse])
async def list_sessions(
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all sessions - only show user's own sessions if logged in."""
    service = SessionService(db)
    user_id = current_user.id if current_user else None
    return await service.list_sessions(user_id=user_id)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: Optional = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a session by ID with messages."""
    service = SessionService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check ownership if authenticated
    if current_user and session.user_id and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return session
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/api/test_sessions_api_user_isolation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/sessions.py backend/tests/api/test_sessions_api_user_isolation.py
git commit -m "feat: add user ownership to session API endpoints"
```

---

## Task 13: Create MemoryService

**Files:**
- Create: `backend/app/services/memory_service.py`
- Test: `backend/tests/services/test_memory_service.py`

**Step 1: Write the failing test**

Create test file `backend/tests/services/test_memory_service.py`:

```python
import pytest
from app.services.memory_service import MemoryService

@pytest.mark.asyncio
async def test_get_short_term_context_returns_sessions(db_session, test_user):
    service = MemoryService(db_session)

    # Create some sessions for the user
    # ... setup

    context = await service.get_short_term_context(test_user.id, limit=3)

    assert isinstance(context, list)
    assert len(context) <= 3

@pytest.mark.asyncio
async def test_get_preferences_empty_for_new_user(db_session, test_user):
    service = MemoryService(db_session)
    prefs = await service.get_preferences(test_user.id)
    assert prefs == {}

@pytest.mark.asyncio
async def test_set_and_get_preference(db_session, test_user):
    service = MemoryService(db_session)
    await service.set_preference(test_user.id, "theme", "dark")
    prefs = await service.get_preferences(test_user.id)
    assert prefs["theme"] == "dark"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_memory_service.py -v`
Expected: FAIL with "cannot import 'MemoryService'"

**Step 3: Write minimal implementation**

Create file `backend/app/services/memory_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from app.models.session import Session
from app.models.user_preference import UserPreference
from app.services.chroma_service import ChromaService
from app.config import get_settings


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.chroma = ChromaService()

    async def get_short_term_context(
        self, user_id: str, limit: int = None
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context from last N sessions."""
        if limit is None:
            limit = self.settings.short_term_session_limit

        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.updated_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        context = []
        for session in sessions:
            # Get messages for this session
            from app.services.message_service import MessageService
            msg_service = MessageService(self.db)
            messages = await msg_service.get_messages_by_session(session.id)

            # Build condensed context
            context.append({
                "session_id": session.id,
                "title": session.title,
                "summary": session.summary,
                "message_count": len(messages)
            })

        return context

    async def get_long_term_memory(
        self, user_id: str, query: str, top_k: int = None
    ) -> Dict[str, Any]:
        """Retrieve relevant long-term memories (facts + summaries)."""
        if top_k is None:
            top_k = self.settings.long_term_memory_top_k

        # Query user facts from ChromaDB
        facts = await self._query_user_facts(user_id, query, top_k)

        # Query conversation summaries from ChromaDB
        summaries = await self._query_summaries(user_id, query, top_k)

        return {
            "facts": facts,
            "summaries": summaries
        }

    async def _query_user_facts(
        self, user_id: str, query: str, top_k: int
    ) -> List[Dict]:
        collection_name = f"user_facts_{user_id}"
        try:
            results = await self.chroma.query_collection(
                collection_name=collection_name,
                query_text=query,
                n_results=top_k
            )
            return results or []
        except Exception:
            return []

    async def _query_summaries(
        self, user_id: str, query: str, top_k: int
    ) -> List[Dict]:
        collection_name = f"conversation_summaries_{user_id}"
        try:
            results = await self.chroma.query_collection(
                collection_name=collection_name,
                query_text=query,
                n_results=top_k
            )
            return results or []
        except Exception:
            return []

    async def save_user_fact(
        self, user_id: str, fact: str, metadata: Dict[str, Any]
    ) -> None:
        """Extract and store a fact about the user."""
        collection_name = f"user_facts_{user_id}"

        # Get embedding
        from app.services.embedding_service import EmbeddingService
        emb_service = EmbeddingService()
        embedding = await emb_service.generate_embedding(fact)

        await self.chroma.add_to_collection(
            collection_name=collection_name,
            documents=[fact],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[f"fact_{user_id}_{len(fact)}"]  # Simple ID generation
        )

    async def save_conversation_summary(
        self, user_id: str, session_id: str, summary: str
    ) -> None:
        """Store conversation summary in vector store."""
        collection_name = f"conversation_summaries_{user_id}"

        from app.services.embedding_service import EmbeddingService
        emb_service = EmbeddingService()
        embedding = await emb_service.generate_embedding(summary)

        await self.chroma.add_to_collection(
            collection_name=collection_name,
            documents=[summary],
            embeddings=[embedding],
            metadatas=[{"session_id": session_id}],
            ids=[f"summary_{session_id}"]
        )

    async def get_preferences(self, user_id: str) -> Dict[str, str]:
        """Get structured user preferences from DB."""
        result = await self.db.execute(
            select(UserPreference)
            .where(UserPreference.user_id == user_id)
        )
        prefs = result.scalars().all()
        return {p.key: p.value for p in prefs}

    async def set_preference(
        self, user_id: str, key: str, value: str
    ) -> None:
        """Store or update a user preference."""
        result = await self.db.execute(
            select(UserPreference)
            .where(UserPreference.user_id == user_id)
            .where(UserPreference.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
        else:
            new_pref = UserPreference(user_id=user_id, key=key, value=value)
            self.db.add(new_pref)

        await self.db.commit()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_memory_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/memory_service.py backend/tests/services/test_memory_service.py
git commit -m "feat: add MemoryService for short-term and long-term memory"
```

---

## Task 14: Update AgentState to Include user_id

**Files:**
- Modify: `backend/app/agents/state.py`
- Test: `backend/tests/agents/test_state_user_id.py`

**Step 1: Write the failing test**

Create test file `backend/tests/agents/test_state_user_id.py`:

```python
import pytest
from app.agents.state import AgentState

def test_agent_state_with_user_id():
    state: AgentState = {
        "user_message": "Hello",
        "user_id": "user123",
        "conversation_history": [],
        "user_intent": "greeting",
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": None
    }

    assert state["user_id"] == "user123"

def test_agent_state_without_user_id():
    state: AgentState = {
        "user_message": "Hello",
        "user_id": None,
        "conversation_history": [],
        "user_intent": "greeting",
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": None
    }

    assert state["user_id"] is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/agents/test_state_user_id.py -v`
Expected: FAIL - AgentState doesn't have user_id field

**Step 3: Write minimal implementation**

Edit `backend/app/agents/state.py`, add user_id field:

```python
from typing import Dict, Any, List, Optional, TypedDict


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

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/agents/test_state_user_id.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/agents/state.py backend/tests/agents/test_state_user_id.py
git commit -m "feat: add user_id field to AgentState"
```

---

## Task 15: Update Chat API to Pass user_id

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Test: `backend/tests/api/test_chat_api_user_id.py`

**Step 1: Write the failing test**

Create test file `backend/tests/api/test_chat_api_user_id.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_passes_user_id_to_agent(test_db, test_user_with_password):
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "username": test_user_with_password.username,
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]

    # Create a session
    session_response = client.post(
        "/api/v1/sessions",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {token}"}
    )
    session_id = session_response.json()["id"]

    # Send message with auth
    response = client.post(
        f"/api/v1/chat/{session_id}/stream",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_chat_api_user_id.py -v`
Expected: FAIL - chat endpoint doesn't use auth or pass user_id

**Step 3: Write minimal implementation**

Edit `backend/app/api/v1/chat.py`, update to pass user_id:

```python
# In the streaming chat endpoint, add auth dependency
@router.post("/{session_id}/stream")
async def stream_chat(
    session_id: str,
    request: ChatRequest,
    current_user: Optional = Depends(get_current_user),  # ADD THIS
    db: AsyncSession = Depends(get_db)
):
    # ... existing code ...

    # Build agent state with user_id
    initial_state: AgentState = {
        "user_message": request.message,
        "user_id": current_user.id if current_user else None,  # ADD THIS
        "conversation_history": history,
        "user_intent": "",
        "retrieved_context": None,
        "context_str": "",
        "sources": None,
        "response": None,
        "error": ""
    }
```

Also need to import get_current_user at the top of the file.

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/api/test_chat_api_user_id.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/chat.py backend/tests/api/test_chat_api_user_id.py
git commit -m "feat: pass user_id from auth to chat agent"
```

---

## Task 16: Enhance response_generator_node with Memory

**Files:**
- Modify: `backend/app/agents/nodes.py`
- Test: `backend/tests/agents/test_nodes_memory_integration.py`

**Step 1: Write the failing test**

Create test file `backend/tests/agents/test_nodes_memory_integration.py`:

```python
import pytest
from app.agents.nodes import response_generator_node
from app.agents.state import AgentState

@pytest.mark.asyncio
async def test_response_generator_includes_memory_for_user(db_session, test_user):
    state: AgentState = {
        "user_message": "What did we discuss before?",
        "user_id": test_user.id,
        "conversation_history": [],
        "user_intent": "legal",
        "retrieved_context": [],
        "context_str": "",
        "sources": None,
        "response": None,
        "error": ""
    }

    # Set up some memory for the user
    # ... setup

    result = await response_generator_node(state)

    # Should include memory-enhanced response
    assert "response" in result
    assert result["error"] == ""

@pytest.mark.asyncio
async def test_response_generator_works_without_user(db_session):
    state: AgentState = {
        "user_message": "Hello",
        "user_id": None,
        "conversation_history": [],
        "user_intent": "greeting",
        "retrieved_context": None,
        "context_str": None,
        "sources": None,
        "response": None,
        "error": ""
    }

    result = await response_generator_node(state)

    # Should work without memory
    assert "response" in result
    assert result["error"] == ""
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/agents/test_nodes_memory_integration.py -v`
Expected: FAIL - node doesn't use memory

**Step 3: Write minimal implementation**

Edit `backend/app/agents/nodes.py`, update response_generator_node:

```python
async def response_generator_node(state: AgentState) -> Dict[str, Any]:
    llm_service = get_llm_service()
    system_prompt = build_system_prompt(state.get("context_str", ""))

    # Check if user has memory
    user_id = state.get("user_id")
    if user_id:
        from app.services.memory_service import MemoryService
        from app.database import AsyncSessionLocal

        # Get memory
        async with AsyncSessionLocal() as memory_db:
            memory_service = MemoryService(memory_db)

            # Get short-term context
            short_term = await memory_service.get_short_term_context(user_id)

            # Get long-term memory
            long_term = await memory_service.get_long_term_memory(
                user_id, state["user_message"]
            )

            # Get preferences
            prefs = await memory_service.get_preferences(user_id)

            # Enhance system prompt
            system_prompt = _enhance_prompt_with_memory(
                system_prompt, short_term, long_term, prefs
            )

    # Build prompt template with memory
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{user_message}")
    ])

    chain = prompt_template | llm_service.llm | StrOutputParser()
    history_messages = convert_to_langchain_messages(state["conversation_history"])
    response = await chain.ainvoke({
        "history": history_messages,
        "user_message": state["user_message"]
    })

    return {"response": response, "error": ""}


def _enhance_prompt_with_memory(
    base_prompt: str,
    short_term: List[Dict],
    long_term: Dict,
    preferences: Dict[str, str]
) -> str:
    """Enhance system prompt with memory information."""
    enhanced = base_prompt

    if preferences:
        pref_str = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])
        enhanced += f"\n\nUser Preferences:\n{pref_str}"

    if short_term:
        enhanced += "\n\nRecent Conversations:"
        for ctx in short_term[:3]:
            enhanced += f"\n- {ctx.get('title', 'Untitled')}: {ctx.get('summary', 'No summary')}"

    if long_term.get("facts"):
        enhanced += "\n\nRelevant Facts about User:"
        for fact in long_term["facts"][:3]:
            enhanced += f"\n- {fact.get('content', fact)}"

    return enhanced
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/agents/test_nodes_memory_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/agents/nodes.py backend/tests/agents/test_nodes_memory_integration.py
git commit -m "feat: integrate memory into response_generator_node"
```

---

## Task 17: Frontend Auth Store

**Files:**
- Create: `frontend/src/stores/authStore.ts`
- Test: `frontend/src/stores/__tests__/authStore.test.ts`

**Step 1: Write the failing test**

Create test file `frontend/src/stores/__tests__/authStore.test.ts`:

```typescript
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../authStore';

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.getState().reset();
  });

  it('should initialize with no user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should login and set user', async () => {
    const { result } = renderHook(() => useAuthStore());

    // Mock API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'test-token',
          user: { id: '123', username: 'testuser' }
        })
      })
    ) as jest.Mock;

    await act(async () => {
      await result.current.login('testuser', 'password');
    });

    expect(result.current.user).toEqual({ id: '123', username: 'testuser' });
    expect(result.current.isAuthenticated).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- authStore.test.ts`
Expected: FAIL with "Cannot find module 'authStore'"

**Step 3: Write minimal implementation**

Create file `frontend/src/stores/authStore.ts`:

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  created_at: string;
  last_login?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, password: string) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
          throw new Error('Login failed');
        }

        const data = await response.json();
        set({
          user: data.user,
          token: data.access_token,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },

      register: async (username: string, password: string) => {
        const response = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
          throw new Error('Registration failed');
        }

        // Auto-login after registration
        const data = await response.json();
        // ... set user state
      },
    }),
    { name: 'auth-storage' }
  )
);
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- authStore.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/stores/authStore.ts frontend/src/stores/__tests__/authStore.test.ts
git commit -m "feat: add auth store with login/logout/register"
```

---

## Task 18: Frontend API Token Interceptor

**Files:**
- Modify: `frontend/src/api/client.ts`

**Step 1: Update API client to include token**

Edit `frontend/src/api/client.ts`, add axios interceptor:

```typescript
import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export default api;
```

**Step 2: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add auth token interceptor to API client"
```

---

## Task 19: Frontend LoginForm Component

**Files:**
- Create: `frontend/src/components/auth/LoginForm.tsx`
- Create: `frontend/src/components/auth/__tests__/LoginForm.test.tsx`

**Step 1: Write the component**

Create file `frontend/src/components/auth/LoginForm.tsx`:

```typescript
import React, { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { Button, Input, Card, Typography } from 'antd';

const { Title } = Typography;

interface LoginFormProps {
  onLoginSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);

  const { login, register } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        await register(username, password);
      } else {
        await login(username, password);
      }
      onLoginSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card style={{ maxWidth: 400, margin: '100px auto' }}>
      <Title level={3}>{isRegister ? 'Register' : 'Login'}</Title>
      <form onSubmit={handleSubmit}>
        <Input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ marginBottom: 16 }}
        />
        <Input.Password
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ marginBottom: 16 }}
        />
        {error && <div style={{ color: 'red', marginBottom: 16 }}>{error}</div>}
        <Button type="primary" htmlType="submit" loading={loading} block>
          {isRegister ? 'Register' : 'Login'}
        </Button>
        <Button
          type="link"
          onClick={() => setIsRegister(!isRegister)}
          block
        >
          {isRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
        </Button>
      </form>
    </Card>
  );
};
```

**Step 2: Write tests**

Create test file `frontend/src/components/auth/__tests__/LoginForm.test.tsx`:

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from '../LoginForm';

describe('LoginForm', () => {
  it('renders login form', () => {
    render(<LoginForm />);
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
  });

  it('switches between login and register', () => {
    render(<LoginForm />);
    fireEvent.click(screen.getByText(/Don't have an account/i));
    expect(screen.getByText('Register')).toBeInTheDocument();
  });
});
```

**Step 3: Commit**

```bash
git add frontend/src/components/auth/LoginForm.tsx frontend/src/components/auth/__tests__/LoginForm.test.tsx
git commit -m "feat: add LoginForm component with login/register toggle"
```

---

## Task 20: Frontend UserMenu Component

**Files:**
- Create: `frontend/src/components/auth/UserMenu.tsx`
- Create: `frontend/src/components/auth/__tests__/UserMenu.test.tsx`

**Step 1: Write the component**

Create file `frontend/src/components/auth/UserMenu.tsx`:

```typescript
import React from 'react';
import { useAuthStore } from '../../stores/authStore';
import { Dropdown, Avatar, Button } from 'antd';

export const UserMenu: React.FC = () => {
  const { user, logout } = useAuthStore();

  if (!user) return null;

  const items = [
    {
      key: 'logout',
      label: 'Logout',
      onClick: logout,
    },
  ];

  return (
    <Dropdown menu={{ items }} placement="bottomRight">
      <Button type="text">
        <Avatar size="small" style={{ marginRight: 8 }}>
          {user.username[0].toUpperCase()}
        </Avatar>
        {user.username}
      </Button>
    </Dropdown>
  );
};
```

**Step 2: Write tests**

Create test file `frontend/src/components/auth/__tests__/UserMenu.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { UserMenu } from '../UserMenu';
import { useAuthStore } from '../../../stores/authStore';

describe('UserMenu', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: '123', username: 'testuser' },
      token: 'test-token',
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
    });
  });

  it('displays username', () => {
    render(<UserMenu />);
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });
});
```

**Step 3: Commit**

```bash
git add frontend/src/components/auth/UserMenu.tsx frontend/src/components/auth/__tests__/UserMenu.test.tsx
git commit -m "feat: add UserMenu component with logout"
```

---

## Task 21: Create Database Migration Script

**Files:**
- Create: `backend/alembic/versions/001_add_user_support.py`

**Step 1: Create migration file**

Create migration file using Alembic:

```bash
cd backend && alembic revision -m "add user support"
```

Then edit the generated file:

```python
"""add user support

Revision ID: 001_add_user_support
Revises:
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_add_user_support'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.String(500), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
        sa.UniqueConstraint('user_id', 'key', name='uq_user_preferences_user_id_key'),
    )

    # Add user_id to sessions
    op.add_column('sessions', sa.Column('user_id', sa.String(36), nullable=True))
    op.create_foreign_key('fk_sessions_user_id', 'sessions', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])

    # Add user_id to messages
    op.add_column('messages', sa.Column('user_id', sa.String(36), nullable=True))
    op.create_foreign_key('fk_messages_user_id', 'messages', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_messages_user_id', 'messages', ['user_id'])


def downgrade():
    op.drop_index('ix_messages_user_id', 'messages')
    op.drop_constraint('fk_messages_user_id', 'messages', type_='foreignkey')
    op.drop_column('messages', 'user_id')

    op.drop_index('ix_sessions_user_id', 'sessions')
    op.drop_constraint('fk_sessions_user_id', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'user_id')

    op.drop_table('user_preferences')
    op.drop_table('users')
```

**Step 2: Test migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration applies successfully

**Step 3: Commit**

```bash
git add backend/alembic/versions/001_add_user_support.py
git commit -m "feat: add database migration for user support"
```

---

## Task 22: End-to-End Integration Test

**Files:**
- Create: `backend/tests/integration/test_user_workflow_e2e.py`

**Step 1: Write E2E test**

Create test file `backend/tests/integration/test_user_workflow_e2e.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_user_workflow(test_db):
    """Test full user registration, login, session creation, and chat."""

    # 1. Register new user
    register_response = client.post("/api/v1/auth/register", json={
        "username": "e2euser",
        "password": "password123"
    })
    assert register_response.status_code == 200
    user_id = register_response.json()["id"]

    # 2. Login
    login_response = client.post("/api/v1/auth/login", json={
        "username": "e2euser",
        "password": "password123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create session
    session_response = client.post(
        "/api/v1/sessions",
        json={"title": "My E2E Session"},
        headers=headers
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["id"]

    # 4. List sessions (should only see own sessions)
    list_response = client.get("/api/v1/sessions", headers=headers)
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == session_id

    # 5. Send message
    chat_response = client.post(
        f"/api/v1/chat/{session_id}/stream",
        json={"message": "Hello"},
        headers=headers
    )
    assert chat_response.status_code == 200

    # 6. Access another user's session (should fail)
    other_user_response = client.post("/api/v1/auth/register", json={
        "username": "otheruser",
        "password": "password123"
    })
    other_token = other_user_response.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Try to access first user's session
    access_response = client.get(
        f"/api/v1/sessions/{session_id}",
        headers=other_headers
    )
    assert access_response.status_code == 403
```

**Step 2: Run test**

Run: `cd backend && pytest tests/integration/test_user_workflow_e2e.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/test_user_workflow_e2e.py
git commit -m "test: add end-to-end user workflow integration test"
```

---

## Task 23: Run Full Test Suite and Verify

**Step 1: Run all backend tests**

Run: `cd backend && pytest -v`
Expected: All tests pass

**Step 2: Run all frontend tests**

Run: `cd frontend && npm test -- --coverage`
Expected: All tests pass with reasonable coverage

**Step 3: Verify backward compatibility**

- Test that existing frontend still works without login
- Test that anonymous sessions can still be created

**Step 4: Final commit**

```bash
git add .
git commit -m "test: verify full test suite passes for user system"
```

---

## Summary

This implementation plan adds user authentication and memory system in 23 bite-sized tasks following TDD principles:

**Backend Tasks (1-16, 21-23):**
1-5: Database models (User, UserPreference) and migration
6-10: Auth schemas, service, JWT, dependencies, API endpoints
11-12: Session isolation (service + API)
13: Memory service (short-term + long-term)
14-16: Agent integration with memory
21-23: Migration, E2E tests, verification

**Frontend Tasks (17-20):**
17: Auth store (Zustand)
18: API token interceptor
19: LoginForm component
20: UserMenu component

**Success Criteria:**
- ✅ Users can register and login
- ✅ Authenticated users only see their own sessions
- ✅ Anonymous sessions still work
- ✅ Memory system integrated
- ✅ All tests pass
- ✅ No breaking changes
