"""Transaction schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class TransactionCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    amount: Decimal = Field(..., gt=0)
    account_id: int
    category_id: Optional[int] = None
    date: date
    note: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)
    transfer_account_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    amount: Optional[Decimal] = Field(None, gt=0)
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    date: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100)
    transfer_account_id: Optional[int] = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int] = None
    type: str
    amount: Decimal
    date: date
    note: Optional[str] = None
    reference: Optional[str] = None
    transfer_account_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionFilters(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    type: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
