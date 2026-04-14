"""Account service."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountUpdate


def get_accounts(db: Session, user_id: int, include_inactive: bool = False) -> List[Account]:
    """Get all accounts for a user."""
    query = db.query(Account).filter(Account.user_id == user_id)
    
    if not include_inactive:
        query = query.filter(Account.is_active == True)
    
    return query.all()


def get_account(db: Session, account_id: int, user_id: int) -> Account:
    """Get a specific account by ID."""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account


def create_account(db: Session, user_id: int, account_data: AccountCreate) -> Account:
    """Create a new account."""
    account = Account(
        user_id=user_id,
        name=account_data.name,
        type=account_data.type,
        currency=account_data.currency,
        opening_balance=account_data.opening_balance,
        current_balance=account_data.opening_balance,
        is_active=True
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account


def update_account(db: Session, account_id: int, user_id: int, account_data: AccountUpdate) -> Account:
    """Update an account."""
    account = get_account(db, account_id, user_id)
    
    update_data = account_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    return account


def delete_account(db: Session, account_id: int, user_id: int) -> None:
    """Delete/archive an account."""
    account = get_account(db, account_id, user_id)
    
    # Check if account has transactions
    transaction_count = db.query(func.count(Transaction.id)).filter(
        Transaction.account_id == account_id
    ).scalar()
    
    if transaction_count > 0:
        # Archive instead of delete
        account.is_active = False
        db.commit()
    else:
        db.delete(account)
        db.commit()


def recalculate_balance(db: Session, account_id: int) -> None:
    """Recalculate account balance from transactions."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return
    
    # Calculate balance from transactions
    income_total = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.account_id == account_id,
        Transaction.type == "income"
    ).scalar()
    
    expense_total = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.account_id == account_id,
        Transaction.type == "expense"
    ).scalar()
    
    account.current_balance = account.opening_balance + income_total - expense_total
    db.commit()
