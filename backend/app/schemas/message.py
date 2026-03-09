from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from typing import Any, Optional, Union
from typing_extensions import Literal
import json


class MessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    session_id: Optional[str] = None


class MessageResponse(MessageBase):
    id: str
    session_id: str
    created_at: datetime
    msg_metadata: Any = None

    @classmethod
    def from_message_obj(cls, obj):
        """Create from SQLAlchemy Message object"""
        # Get the raw metadata from the database column
        metadata_raw = getattr(obj, '_msg_metadata', None)
        metadata_dict = None
        if metadata_raw:
            try:
                metadata_dict = json.loads(metadata_raw)
            except:
                pass

        return cls(
            id=str(obj.id),
            session_id=str(obj.session_id),
            role=obj.role,
            content=obj.content,
            created_at=obj.created_at,
            msg_metadata=metadata_dict
        )


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)


class ChatStreamChunk(BaseModel):
    type: Literal["token", "error", "done", "citation"]
    data: Union[str, dict]
