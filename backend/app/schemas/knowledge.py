from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Literal


class KnowledgeDocumentBase(BaseModel):
    title: str = Field(..., max_length=255)
    category: Optional[Literal["law", "case", "contract", "interpretation"]] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=500)


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: UUID
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)
    category: Optional[str] = None


class SearchResult(BaseModel):
    text: str
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict
