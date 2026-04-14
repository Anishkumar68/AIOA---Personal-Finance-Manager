"""Budget API routes."""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services import budget_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("/", response_model=List[dict])
def get_budgets(
    month: Optional[date] = Query(None),
    include_progress: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for the current user."""
    if include_progress:
        return budget_service.get_budget_progress(db, current_user.id, month)
    else:
        return budget_service.get_budgets(db, current_user.id, month)


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new budget."""
    return budget_service.create_budget(db, current_user.id, budget_data)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a budget."""
    return budget_service.update_budget(db, budget_id, current_user.id, budget_data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a budget."""
    budget_service.delete_budget(db, budget_id, current_user.id)
    return None
