from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.schemas.message import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and get a response"""
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

    # Generate a simple response (placeholder for LLM)
    response_content = f"你说: {request.message}\n\n这是一个测试回复。完整的 AI 功能正在开发中。"

    # Save the exchange
    await message_service.save_exchange(
        session_id,
        request.message,
        response_content,
        {"type": "test_response"}
    )

    # Update session
    await session_service.increment_message_count(session_id)

    return {
        "session_id": str(session_id),
        "response": response_content,
        "sources": []
    }
