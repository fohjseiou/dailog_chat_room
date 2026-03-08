from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    source = Column(String(500), nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    VALID_CATEGORIES = {"law", "case", "contract", "interpretation"}
