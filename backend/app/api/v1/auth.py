"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.services.auth_service import AuthService, UserAlreadyExistsError, InvalidCredentialsError
from app.services.token_service import TokenService
from app.schemas.user import UserCreate, UserResponse, TokenResponse
from app.models.user import User
from app.dependencies import get_current_user_dep

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=200)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Args:
        user_data: User creation data with username and password
        db: Database session

    Returns:
        UserResponse: Created user information

    Raises:
        HTTPException 400: If username already exists
    """
    service = AuthService(db)
    try:
        user = await service.register(user_data)
        return user
    except UserAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Username already exists")


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    credentials: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.

    Args:
        credentials: Dictionary containing username and password
        db: Database session

    Returns:
        TokenResponse: JWT access token and user information

    Raises:
        HTTPException 401: If credentials are invalid
    """
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(status_code=422, detail="Username and password are required")

    service = AuthService(db)
    token_service = TokenService()

    try:
        # Authenticate user
        user = await service.login(username, password)

        # Update last_login
        user.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(user)

        # Create JWT token
        access_token = token_service.create_access_token(user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse, status_code=200)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_dep)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token (required)

    Returns:
        UserResponse: Current user information

    Raises:
        HTTPException 401: If not authenticated
    """
    return UserResponse.model_validate(current_user)
