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
