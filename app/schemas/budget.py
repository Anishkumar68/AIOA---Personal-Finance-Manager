"""Budget schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class BudgetCreate(BaseModel):
    category_id: int
    month: date
    amount: Decimal = Field(..., gt=0)


class BudgetUpdate(BaseModel):
    amount: Decimal = Field(..., gt=0)


class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category_id: int
    month: date
    amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
