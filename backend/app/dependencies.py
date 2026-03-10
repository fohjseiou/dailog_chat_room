"""FastAPI dependencies for authentication."""

from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.token_service import TokenService
from app.services.auth_service import AuthService
from app.models.user import User
from app.database import get_db


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token.

    Returns None if no token provided (anonymous access).
    Returns None if token is invalid (treat as anonymous for user-friendliness).

    Args:
        authorization: The Authorization header value (format: "Bearer <token>")
        db: Database session dependency

    Returns:
        User object if token is valid, None otherwise
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

        if not user_id:
            return None

        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(user_id)
        return user

    except Exception:
        # Invalid token - treat as anonymous
        return None


async def get_current_user_dep(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency wrapper for get_current_user that raises HTTPException if not authenticated.

    Use this when authentication is required (not optional).

    Args:
        authorization: The Authorization header value (format: "Bearer <token>")
        db: Database session dependency

    Returns:
        User object if token is valid

    Raises:
        HTTPException: If token is missing or invalid
    """
    user = await get_current_user(authorization, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
