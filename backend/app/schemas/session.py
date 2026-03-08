from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SessionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: str = Field(..., max_length=255)


class SessionResponse(SessionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    id: UUID
    title: Optional[str]
    created_at: datetime
    summary: Optional[str] = None
    message_count: int

    class Config:
        from_attributes = True
