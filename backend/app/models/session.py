from sqlalchemy import Column, String, Text, Integer, DateTime, func
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
    user_id = Column(String(36), nullable=True)

    # relationships - specify primaryjoin since no database FK
    messages = relationship(
        "Message",
        back_populates="session",
        primaryjoin="Session.id == Message.session_id",
        foreign_keys="Message.session_id",
        cascade="all, delete-orphan"
    )
    user = relationship(
        "User",
        back_populates="sessions",
        primaryjoin="Session.user_id == User.id",
        foreign_keys="Session.user_id"
    )
