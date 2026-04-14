"""Loan (Udhar Khata) schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime, date
from decimal import Decimal


LoanDirection = Literal["lent", "borrowed"]
LoanStatus = Literal["open", "closed"]
LoanEntryKind = Literal["disbursement", "repayment"]


class LoanEntryCreate(BaseModel):
    kind: LoanEntryKind
    amount: Decimal = Field(..., gt=0)
    occurred_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=500)


class LoanEntryResponse(BaseModel):
    id: int
    user_id: int
    loan_id: int
    kind: str
    amount: Decimal
    occurred_at: datetime
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoanCreate(BaseModel):
    contact_id: int
    direction: LoanDirection
    title: Optional[str] = Field(None, max_length=120)
    currency: str = Field(default="INR", min_length=1, max_length=10)
    interest_rate: Optional[Decimal] = Field(None, ge=0)
    start_date: date
    due_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)

    initial_amount: Decimal = Field(..., gt=0)
    initial_occurred_at: Optional[datetime] = None
    initial_note: Optional[str] = Field(None, max_length=500)


class LoanUpdate(BaseModel):
    contact_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=120)
    currency: Optional[str] = Field(None, min_length=1, max_length=10)
    interest_rate: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[LoanStatus] = None


class LoanResponse(BaseModel):
    id: int
    user_id: int
    contact_id: int
    direction: str
    status: str
    title: Optional[str] = None
    currency: str
    interest_rate: Optional[Decimal] = None
    start_date: date
    due_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    contact_name: str
    total_disbursed: Decimal
    total_repaid: Decimal
    outstanding: Decimal
    last_activity_at: Optional[datetime] = None
    entries: Optional[List[LoanEntryResponse]] = None
