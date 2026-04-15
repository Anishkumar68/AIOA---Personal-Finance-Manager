"""Recurring Transaction Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal


class RecurringTransactionBase(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    type: str  # income, expense, transfer
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    frequency: str  # daily, weekly, monthly, yearly
    interval: int = Field(default=1, ge=1)
    start_date: date
    end_date: Optional[date] = None
    note: Optional[str] = None
    reference: Optional[str] = None
    transfer_account_id: Optional[int] = None


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionUpdate(BaseModel):
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    type: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    frequency: Optional[str] = None
    interval: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    note: Optional[str] = None
    reference: Optional[str] = None
    transfer_account_id: Optional[int] = None
    is_active: Optional[bool] = None


class RecurringTransactionResponse(RecurringTransactionBase):
    id: int
    user_id: int
    next_occurrence: date
    is_active: bool
    last_processed: Optional[date] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
