from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class SessionBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: str = Field(..., max_length=255)


class SessionResponse(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    message_count: int
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    message_count: int
    user_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
