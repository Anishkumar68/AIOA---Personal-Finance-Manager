"""Recurring Transaction API routes."""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.recurring_transaction import RecurringTransaction
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    RecurringTransactionResponse,
    RecurringTransactionListResponse,
)
from app.services import recurring_transaction_service as service

router = APIRouter(prefix="/recurring", tags=["recurring-transactions"])


@router.get("/", response_model=RecurringTransactionListResponse)
def get_recurring_transactions(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all recurring transactions for the current user."""
    recurring_list = service.get_recurring_transactions(db, current_user.id, include_inactive)
    
    return {
        "items": recurring_list,
        "total": len(recurring_list)
    }


@router.post("/", response_model=RecurringTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_transaction(
    recurring_data: RecurringTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new recurring transaction."""
    return service.create_recurring_transaction(db, current_user.id, recurring_data)


@router.get("/{recurring_id}", response_model=RecurringTransactionResponse)
def get_recurring_transaction(
    recurring_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific recurring transaction."""
    return service.get_recurring_transaction(db, recurring_id, current_user.id)


@router.put("/{recurring_id}", response_model=RecurringTransactionResponse)
def update_recurring_transaction(
    recurring_id: int,
    recurring_data: RecurringTransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a recurring transaction."""
    return service.update_recurring_transaction(db, recurring_id, current_user.id, recurring_data)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_transaction(
    recurring_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a recurring transaction."""
    service.delete_recurring_transaction(db, recurring_id, current_user.id)
    return None


@router.post("/process")
def process_recurring_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process all due recurring transactions and create actual transactions.
    
    This endpoint is typically called by a background job or scheduler.
    """
    created_count = service.process_due_recurring_transactions(db, current_user.id)
    
    return {
        "message": f"Processed {created_count} recurring transaction(s)",
        "created_count": created_count
    }
