"""Goal (savings target) schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    currency: str = Field("INR", min_length=3, max_length=3)
    target_amount: Decimal = Field(..., gt=0)
    start_date: date
    target_date: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class GoalContributionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    date: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)


class GoalContributionResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    amount: Decimal
    date: date
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GoalResponse(BaseModel):
    id: int
    user_id: int
    name: str
    currency: str
    target_amount: Decimal
    start_date: date
    target_date: Optional[date]
    note: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoalProgressResponse(GoalResponse):
    saved_amount: Decimal
    remaining_amount: Decimal
    progress_pct: float
    is_completed: bool
    contributions_count: int


class GoalDetailResponse(GoalProgressResponse):
    contributions: List[GoalContributionResponse] = []

