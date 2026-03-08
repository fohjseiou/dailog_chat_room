from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, data: MessageCreate) -> MessageResponse:
        message = Message(
            session_id=data.session_id or UUID("00000000-0000-0000-0000-000000000000"),
            role=data.role,
            content=data.content
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return MessageResponse.model_validate(message)

    async def get_messages_by_session(self, session_id: UUID) -> List[MessageResponse]:
        messages = await Message.get_by_session(self.db, session_id)
        return [MessageResponse.model_validate(m) for m in messages]

    async def save_exchange(self, session_id: UUID, user_message: str, assistant_message: str, metadata: dict = None):
        """Save both user and assistant messages"""
        user_msg = Message(
            session_id=session_id,
            role="user",
            content=user_message
        )
        self.db.add(user_msg)

        asst_msg = Message(
            session_id=session_id,
            role="assistant",
            content=assistant_message,
            metadata=metadata or {}
        )
        self.db.add(asst_msg)

        await self.db.commit()
        await self.db.refresh(user_msg)
        await self.db.refresh(asst_msg)

        return MessageResponse.model_validate(user_msg), MessageResponse.model_validate(asst_msg)
