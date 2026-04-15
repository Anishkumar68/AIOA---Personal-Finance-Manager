"""Tag Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class TagResponse(TagBase):
    id: int
    user_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
