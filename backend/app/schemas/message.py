from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, Literal


class MessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    session_id: Optional[UUID] = None


class MessageResponse(MessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str = Field(..., min_length=1)


class ChatStreamChunk(BaseModel):
    type: Literal["token", "error", "done", "citation"]
    data: str | Dict[str, Any]
