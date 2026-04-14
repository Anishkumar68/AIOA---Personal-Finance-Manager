"""Account schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    currency: str = Field(default="INR", max_length=10)
    opening_balance: Decimal = Field(default=0, ge=0)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    currency: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    currency: str
    opening_balance: Decimal
    current_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
