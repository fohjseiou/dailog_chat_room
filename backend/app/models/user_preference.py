from sqlalchemy import Column, String, DateTime, func
from app.database import Base
import uuid


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # No foreign key - just store the user_id as string
    user_id = Column(String(36), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())