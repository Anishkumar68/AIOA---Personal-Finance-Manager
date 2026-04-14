"""Loan (Udhar Khata) API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanUpdate, LoanResponse, LoanEntryCreate, LoanEntryResponse
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/", response_model=dict)
def get_loans(
    direction: Optional[str] = Query(None),
    status_value: Optional[str] = Query(None, alias="status"),
    contact_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    items, total = loan_service.list_loans(
        db,
        current_user.id,
        direction=direction,
        status_value=status_value,
        contact_id=contact_id,
        search=search,
        page=page,
        limit=limit,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
    }


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return loan_service.create_loan(db, current_user.id, payload)


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return loan_service.get_loan(db, loan_id, current_user.id, include_entries=True)


@router.put("/{loan_id}", response_model=LoanResponse)
def update_loan(
    loan_id: int,
    payload: LoanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return loan_service.update_loan(db, loan_id, current_user.id, payload)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    loan_service.delete_loan(db, loan_id, current_user.id)
    return None


@router.get("/{loan_id}/entries", response_model=list[LoanEntryResponse])
def get_entries(
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return loan_service.list_entries(db, loan_id, current_user.id)


@router.post("/{loan_id}/entries", response_model=LoanEntryResponse, status_code=status.HTTP_201_CREATED)
def add_entry(
    loan_id: int,
    payload: LoanEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return loan_service.add_entry(db, loan_id, current_user.id, payload)


@router.delete("/{loan_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    loan_id: int,
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    loan_service.delete_entry(db, loan_id, entry_id, current_user.id)
    return None

