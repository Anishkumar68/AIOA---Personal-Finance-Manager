"""Contact schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ContactResponse(BaseModel):
    id: int
    user_id: int
    name: str
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

