from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, data: MessageCreate) -> MessageResponse:
        message = Message(
            session_id=data.session_id or "00000000-0000-0000-0000-000000000000",
            role=data.role,
            content=data.content
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return MessageResponse.from_message_obj(message)

    async def get_messages_by_session(self, session_id: str) -> List[MessageResponse]:
        messages = await Message.get_by_session(self.db, session_id)
        return [MessageResponse.from_message_obj(m) for m in messages]

    async def save_exchange(self, session_id: str, user_message: str, assistant_message: str, metadata: dict = None):
        """Save both user and assistant messages"""
        user_msg = Message(
            session_id=session_id,
            role="user",
            content=user_message
        )
        self.db.add(user_msg)

        # The hybrid_property setter will handle JSON conversion
        asst_msg = Message(
            session_id=session_id,
            role="assistant",
            content=assistant_message,
            msg_metadata=metadata or {}
        )
        self.db.add(asst_msg)

        await self.db.commit()
        await self.db.refresh(user_msg)
        await self.db.refresh(asst_msg)

        return MessageResponse.from_message_obj(user_msg), MessageResponse.from_message_obj(asst_msg)

    async def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID"""
        message = await self.db.execute(select(Message).where(Message.id == message_id))
        message_obj = message.scalar_one_or_none()

        if message_obj:
            await self.db.delete(message_obj)
            await self.db.commit()
            return True
        return False
