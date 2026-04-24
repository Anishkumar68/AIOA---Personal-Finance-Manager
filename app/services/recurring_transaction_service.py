"""Recurring Transaction service."""

from typing import List, Tuple
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.schemas.recurring_transaction import RecurringTransactionCreate, RecurringTransactionUpdate

logger = logging.getLogger(__name__)

def get_recurring_transactions(
    db: Session,
    user_id: int,
    include_inactive: bool = False
) -> List[RecurringTransaction]:
    """Get all recurring transactions for a user."""
    query = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id
    )
    
    if not include_inactive:
        query = query.filter(RecurringTransaction.is_active == True)
    
    return query.order_by(RecurringTransaction.next_occurrence.asc()).all()


def get_recurring_transaction(db: Session, recurring_id: int, user_id: int) -> RecurringTransaction:
    """Get a specific recurring transaction by ID."""
    recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.id == recurring_id,
        RecurringTransaction.user_id == user_id
    ).first()

    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring transaction not found"
        )

    return recurring


def create_recurring_transaction(
    db: Session, 
    user_id: int, 
    recurring_data: RecurringTransactionCreate
) -> RecurringTransaction:
    """Create a new recurring transaction."""
    # Validate account exists and belongs to user
    account = db.query(Account).filter(
        Account.id == recurring_data.account_id,
        Account.user_id == user_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create recurring transaction for archived account"
        )

    # Validate category if provided
    if recurring_data.category_id:
        category = db.query(Category).filter(
            Category.id == recurring_data.category_id,
            Category.user_id == user_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use archived category"
            )

        # Validate category type matches transaction type
        if recurring_data.type == "income" and category.type != "income":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use expense category for income transaction"
            )

        if recurring_data.type == "expense" and category.type != "expense":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use income category for expense transaction"
            )

    # Validate transfer
    if recurring_data.type == "transfer":
        if not recurring_data.transfer_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer requires transfer_account_id"
            )

        transfer_account = db.query(Account).filter(
            Account.id == recurring_data.transfer_account_id,
            Account.user_id == user_id
        ).first()

        if not transfer_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer account not found"
            )

        if not transfer_account.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to archived account"
            )

    # Calculate next occurrence
    next_occurrence = recurring_data.start_date

    # Create recurring transaction
    recurring = RecurringTransaction(
        user_id=user_id,
        account_id=recurring_data.account_id,
        category_id=recurring_data.category_id,
        type=recurring_data.type,
        amount=recurring_data.amount,
        frequency=recurring_data.frequency,
        interval=recurring_data.interval,
        start_date=recurring_data.start_date,
        end_date=recurring_data.end_date,
        next_occurrence=next_occurrence,
        note=recurring_data.note,
        reference=recurring_data.reference,
        transfer_account_id=recurring_data.transfer_account_id,
        is_active=True,
    )

    db.add(recurring)
    db.commit()
    db.refresh(recurring)

    return recurring


def update_recurring_transaction(
    db: Session,
    recurring_id: int,
    user_id: int,
    recurring_data: RecurringTransactionUpdate
) -> RecurringTransaction:
    """Update a recurring transaction."""
    recurring = get_recurring_transaction(db, recurring_id, user_id)

    update_data = recurring_data.model_dump(exclude_unset=True)

    # Validate account if changed
    if "account_id" in update_data and update_data["account_id"]:
        account = db.query(Account).filter(
            Account.id == update_data["account_id"],
            Account.user_id == user_id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        if not account.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use archived account"
            )

    # Validate category if changed
    if "category_id" in update_data and update_data["category_id"]:
        category = db.query(Category).filter(
            Category.id == update_data["category_id"],
            Category.user_id == user_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use archived category"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(recurring, field, value)

    # Recalculate next occurrence if frequency, interval, or start_date changed
    if any(field in update_data for field in ["frequency", "interval", "start_date"]):
        recurring.next_occurrence = calculate_next_occurrence(
            frequency=recurring.frequency,
            interval=recurring.interval,
            start_date=recurring.start_date,
            last_processed=recurring.last_processed
        )

    db.commit()
    db.refresh(recurring)

    return recurring


def delete_recurring_transaction(db: Session, recurring_id: int, user_id: int) -> None:
    """Delete a recurring transaction."""
    recurring = get_recurring_transaction(db, recurring_id, user_id)
    db.delete(recurring)
    db.commit()


def calculate_next_occurrence(
    frequency: str,
    interval: int,
    start_date: date,
    last_processed: date | datetime | None = None
) -> date:
    """Calculate the next occurrence date based on frequency and interval."""
    if isinstance(last_processed, datetime):
        base_date = last_processed.date()
    else:
        base_date = last_processed or start_date
    
    if frequency == "daily":
        return base_date + timedelta(days=interval)
    elif frequency == "weekly":
        return base_date + timedelta(weeks=interval)
    elif frequency == "monthly":
        # Handle month addition carefully
        month = base_date.month - 1 + interval
        year = base_date.year + month // 12
        month = month % 12 + 1
        day = min(base_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    elif frequency == "yearly":
        try:
            return date(base_date.year + interval, base_date.month, base_date.day)
        except ValueError:
            # Handle leap year
            return date(base_date.year + interval, base_date.month, 28)
    else:
        raise ValueError(f"Invalid frequency: {frequency}")


def process_due_recurring_transactions(db: Session, user_id: int, current_date: date | None = None) -> int:
    """Process all recurring transactions that are due.
    
    Creates actual transactions for recurring entries where next_occurrence <= today.
    Returns the count of transactions created.
    """
    if current_date is None:
        current_date = date.today()

    # Get all active recurring transactions due today or earlier
    due_recurring = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id,
        RecurringTransaction.is_active == True,
        RecurringTransaction.next_occurrence <= current_date,
        or_(
            RecurringTransaction.end_date == None,
            RecurringTransaction.next_occurrence <= RecurringTransaction.end_date
        )
    ).all()

    created_count = 0

    for recurring in due_recurring:
        try:
            # Create the actual transaction
            transaction = Transaction(
                user_id=user_id,
                account_id=recurring.account_id,
                category_id=recurring.category_id,
                type=recurring.type,
                amount=recurring.amount,
                date=recurring.next_occurrence,
                note=recurring.note,
                reference=recurring.reference,
                transfer_account_id=recurring.transfer_account_id,
            )

            db.add(transaction)

            # Update account balances
            if recurring.type == "income":
                db.query(Account).filter(Account.id == recurring.account_id).update(
                    {Account.current_balance: Account.current_balance + recurring.amount}
                )
            elif recurring.type == "expense":
                db.query(Account).filter(Account.id == recurring.account_id).update(
                    {Account.current_balance: Account.current_balance - recurring.amount}
                )
            elif recurring.type == "transfer" and recurring.transfer_account_id:
                db.query(Account).filter(Account.id == recurring.account_id).update(
                    {Account.current_balance: Account.current_balance - recurring.amount}
                )
                db.query(Account).filter(Account.id == recurring.transfer_account_id).update(
                    {Account.current_balance: Account.current_balance + recurring.amount}
                )

            # Update recurring transaction
            recurring.last_processed = datetime.now(timezone.utc)
            recurring.next_occurrence = calculate_next_occurrence(
                frequency=recurring.frequency,
                interval=recurring.interval,
                start_date=recurring.start_date,
                last_processed=recurring.next_occurrence
            )

            # Deactivate if past end_date
            if recurring.end_date and recurring.next_occurrence > recurring.end_date:
                recurring.is_active = False

            created_count += 1

        except Exception as e:
            # Log error but continue processing other recurring transactions
            logger.exception("Error processing recurring transaction id=%s", getattr(recurring, "id", "?"))
            continue

    db.commit()

    return created_count
