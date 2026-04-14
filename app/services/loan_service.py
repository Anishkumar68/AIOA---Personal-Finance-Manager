"""Loan (Udhar Khata) service."""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.contact import Contact
from app.models.loan import Loan
from app.models.loan_entry import LoanEntry
from app.schemas.loan import LoanCreate, LoanUpdate, LoanEntryCreate


def _validate_direction(direction: str) -> None:
    if direction not in {"lent", "borrowed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid direction")


def _validate_status(status_value: str) -> None:
    if status_value not in {"open", "closed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")


def _validate_entry_kind(kind: str) -> None:
    if kind not in {"disbursement", "repayment"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entry kind")


def _loan_totals(loan: Loan) -> Dict[str, Any]:
    total_disbursed = Decimal("0")
    total_repaid = Decimal("0")
    last_activity_at: Optional[datetime] = None

    for entry in loan.entries:
        if entry.kind == "disbursement":
            total_disbursed += Decimal(entry.amount)
        elif entry.kind == "repayment":
            total_repaid += Decimal(entry.amount)

        if last_activity_at is None or entry.occurred_at > last_activity_at:
            last_activity_at = entry.occurred_at

    outstanding = total_disbursed - total_repaid

    q = Decimal("0.01")
    total_disbursed = total_disbursed.quantize(q)
    total_repaid = total_repaid.quantize(q)
    outstanding = outstanding.quantize(q)

    return {
        "total_disbursed": total_disbursed,
        "total_repaid": total_repaid,
        "outstanding": outstanding,
        "last_activity_at": last_activity_at,
    }


def list_loans(
    db: Session,
    user_id: int,
    direction: Optional[str] = None,
    status_value: Optional[str] = None,
    contact_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    query = (
        db.query(Loan)
        .options(joinedload(Loan.contact), joinedload(Loan.entries))
        .filter(Loan.user_id == user_id)
    )

    if direction:
        _validate_direction(direction)
        query = query.filter(Loan.direction == direction)
    if status_value:
        _validate_status(status_value)
        query = query.filter(Loan.status == status_value)
    if contact_id:
        query = query.filter(Loan.contact_id == contact_id)
    if search:
        like = f"%{search}%"
        query = query.join(Loan.contact).filter((Loan.title.ilike(like)) | (Contact.name.ilike(like)))

    total = query.count()

    query = query.order_by(Loan.updated_at.desc(), Loan.created_at.desc())
    offset = (page - 1) * limit
    loans = query.offset(offset).limit(limit).all()

    items: List[Dict[str, Any]] = []
    for loan in loans:
        totals = _loan_totals(loan)
        items.append(
            {
                "id": loan.id,
                "user_id": loan.user_id,
                "contact_id": loan.contact_id,
                "direction": loan.direction,
                "status": loan.status,
                "title": loan.title,
                "currency": loan.currency,
                "interest_rate": loan.interest_rate,
                "start_date": loan.start_date,
                "due_date": loan.due_date,
                "notes": loan.notes,
                "created_at": loan.created_at,
                "updated_at": loan.updated_at,
                "contact_name": loan.contact.name,
                **totals,
            }
        )

    return items, total


def get_loan(db: Session, loan_id: int, user_id: int, include_entries: bool = True) -> Dict[str, Any]:
    q = db.query(Loan).options(joinedload(Loan.contact))
    if include_entries:
        q = q.options(joinedload(Loan.entries))

    loan = q.filter(Loan.id == loan_id, Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    totals = _loan_totals(loan) if include_entries else {"total_disbursed": Decimal("0"), "total_repaid": Decimal("0"), "outstanding": Decimal("0"), "last_activity_at": None}

    result: Dict[str, Any] = {
        "id": loan.id,
        "user_id": loan.user_id,
        "contact_id": loan.contact_id,
        "direction": loan.direction,
        "status": loan.status,
        "title": loan.title,
        "currency": loan.currency,
        "interest_rate": loan.interest_rate,
        "start_date": loan.start_date,
        "due_date": loan.due_date,
        "notes": loan.notes,
        "created_at": loan.created_at,
        "updated_at": loan.updated_at,
        "contact_name": loan.contact.name,
        **totals,
    }
    if include_entries:
        result["entries"] = loan.entries
    return result


def create_loan(db: Session, user_id: int, payload: LoanCreate) -> Dict[str, Any]:
    _validate_direction(payload.direction)

    contact = db.query(Contact).filter(Contact.id == payload.contact_id, Contact.user_id == user_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if not contact.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create loan for inactive contact")

    loan = Loan(
        user_id=user_id,
        contact_id=payload.contact_id,
        direction=payload.direction,
        status="open",
        title=payload.title,
        currency=payload.currency,
        interest_rate=payload.interest_rate,
        start_date=payload.start_date,
        due_date=payload.due_date,
        notes=payload.notes,
    )
    db.add(loan)
    db.flush()  # ensures loan.id exists for entry FK

    entry = LoanEntry(
        user_id=user_id,
        loan_id=loan.id,
        kind="disbursement",
        amount=payload.initial_amount,
        occurred_at=payload.initial_occurred_at or datetime.now(timezone.utc),
        note=payload.initial_note,
    )
    db.add(entry)

    db.commit()
    db.refresh(loan)
    # reload entries for totals
    loan = (
        db.query(Loan)
        .options(joinedload(Loan.contact), joinedload(Loan.entries))
        .filter(Loan.id == loan.id)
        .first()
    )
    return get_loan(db, loan.id, user_id, include_entries=True)


def update_loan(db: Session, loan_id: int, user_id: int, payload: LoanUpdate) -> Dict[str, Any]:
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        _validate_status(update_data["status"])

    if "contact_id" in update_data and update_data["contact_id"] is not None:
        contact = db.query(Contact).filter(Contact.id == update_data["contact_id"], Contact.user_id == user_id).first()
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        if not contact.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot assign inactive contact")

    for field, value in update_data.items():
        setattr(loan, field, value)

    db.commit()
    return get_loan(db, loan.id, user_id, include_entries=True)


def delete_loan(db: Session, loan_id: int, user_id: int) -> None:
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    db.delete(loan)
    db.commit()


def list_entries(db: Session, loan_id: int, user_id: int) -> List[LoanEntry]:
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    return (
        db.query(LoanEntry)
        .filter(LoanEntry.loan_id == loan_id, LoanEntry.user_id == user_id)
        .order_by(LoanEntry.occurred_at.asc(), LoanEntry.created_at.asc())
        .all()
    )


def add_entry(db: Session, loan_id: int, user_id: int, payload: LoanEntryCreate) -> LoanEntry:
    _validate_entry_kind(payload.kind)

    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    if loan.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loan is closed")

    entry = LoanEntry(
        user_id=user_id,
        loan_id=loan_id,
        kind=payload.kind,
        amount=payload.amount,
        occurred_at=payload.occurred_at or datetime.now(timezone.utc),
        note=payload.note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, loan_id: int, entry_id: int, user_id: int) -> None:
    entry = (
        db.query(LoanEntry)
        .filter(
            LoanEntry.id == entry_id,
            LoanEntry.loan_id == loan_id,
            LoanEntry.user_id == user_id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    db.delete(entry)
    db.commit()
