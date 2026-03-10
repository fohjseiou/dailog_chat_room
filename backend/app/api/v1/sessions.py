from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.schemas.message import MessageResponse
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    data: Optional[SessionCreate] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new session"""
    service = SessionService(db)
    # Handle None case for creating session without title
    if data is None:
        data = SessionCreate(title=None)
    user_id = current_user.id if current_user else None
    return await service.create_session(data, user_id=user_id)


@router.get("", response_model=List[SessionListResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """List all sessions"""
    service = SessionService(db)

    # User isolation: authenticated users see only their own sessions
    # Anonymous users see only anonymous sessions (user_id IS NULL)
    if current_user:
        # Authenticated user - show only their sessions
        return await service.list_sessions(user_id=str(current_user.id))
    else:
        # Anonymous user - show only anonymous sessions
        # We need to filter for sessions where user_id IS NULL
        # The service layer returns all sessions when user_id is None,
        # so we filter in the API layer
        all_sessions = await service.list_sessions(user_id=None)
        return [s for s in all_sessions if s.user_id is None]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a session by ID with messages"""
    service = SessionService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ownership check: users can only access their own sessions
    # Anonymous sessions (user_id is None) can be accessed by anyone
    if session.user_id is not None:
        if current_user is None or current_user.id != session.user_id:
            raise HTTPException(status_code=403, detail="Forbidden: You can only access your own sessions")

    return session


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Rename a session"""
    service = SessionService(db)
    try:
        return await service.update_session(session_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a session"""
    from app.services.message_service import MessageService
    service = MessageService(db)
    messages = await service.get_messages_by_session(session_id)
    # The message objects from SQLAlchemy need to be converted to MessageResponse
    # Use the class method we saw in message schema
    return [MessageResponse.from_message_obj(m) for m in messages]


@router.delete("/{session_id}/messages/{message_id}")
async def delete_message(
    session_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific message from a session"""
    from app.services.message_service import MessageService
    service = MessageService(db)
    success = await service.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted"}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a session"""
    service = SessionService(db)
    await service.delete_session(session_id)
    return {"message": "Session deleted"}
