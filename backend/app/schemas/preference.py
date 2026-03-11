from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional


class PreferenceCreate(BaseModel):
    """Schema for creating/updating a single preference"""
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=500)


class PreferenceUpdate(BaseModel):
    """Schema for updating a preference value"""
    value: str = Field(..., min_length=1, max_length=500)


class PreferenceResponse(BaseModel):
    """Schema for a single preference response"""
    id: str
    user_id: str
    key: str
    value: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreferencesResponse(BaseModel):
    """Schema for all preferences response"""
    user_id: str
    preferences: Dict[str, str]
