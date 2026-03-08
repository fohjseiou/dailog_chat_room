from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="cascade"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    metadata = Column(JSONB, nullable=True)

    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_session_id", "session_id"),
    )

    @classmethod
    async def get_by_session(cls, db_session, session_id: uuid.UUID):
        from sqlalchemy import select
        result = await db_session.execute(
            select(cls).where(cls.session_id == session_id).order_by(cls.created_at)
        )
        return result.scalars().all()
