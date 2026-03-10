from sqlalchemy import Column, String, DateTime, ForeignKey, func, Index
from app.database import Base
import uuid


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="cascade"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_user_preferences_user_id_key", "user_id", "key", unique=True),
    )
