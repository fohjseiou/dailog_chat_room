from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Index, Text as JSONColumn
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base
import uuid
import json


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="cascade"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    _msg_metadata = Column("metadata", Text, nullable=True)

    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_session_id", "session_id"),
    )

    @hybrid_property
    def msg_metadata(self):
        if self._msg_metadata:
            try:
                return json.loads(self._msg_metadata)
            except:
                return {}
        return {}

    @msg_metadata.setter
    def msg_metadata(self, value):
        self._msg_metadata = json.dumps(value) if value else None

    @classmethod
    async def get_by_session(cls, db_session, session_id: str):
        from sqlalchemy import select
        result = await db_session.execute(
            select(cls).where(cls.session_id == session_id).order_by(cls.created_at)
        )
        return result.scalars().all()
