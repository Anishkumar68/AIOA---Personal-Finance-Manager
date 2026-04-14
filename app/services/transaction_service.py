"""Transaction service."""

from typing import List, Optional, Tuple
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilters
from app.services.account_service import recalculate_balance


def get_transactions(
    db: Session, 
    user_id: int, 
    filters: TransactionFilters
) -> Tuple[List[Transaction], int]:
    """Get transactions with filters and pagination."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    
    # Apply filters
    if filters.from_date:
        query = query.filter(Transaction.date >= filters.from_date)
    if filters.to_date:
        query = query.filter(Transaction.date <= filters.to_date)
    if filters.account_id:
        query = query.filter(Transaction.account_id == filters.account_id)
    if filters.category_id:
        query = query.filter(Transaction.category_id == filters.category_id)
    if filters.type:
        query = query.filter(Transaction.type == filters.type)
    if filters.search:
        query = query.filter(Transaction.note.ilike(f"%{filters.search}%"))
    
    # Get total count
    total = query.count()
    
    # Order by date desc (newest first) before applying pagination
    query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
    
    # Apply pagination
    offset = (filters.page - 1) * filters.limit
    query = query.offset(offset).limit(filters.limit)
    
    # Execute query
    transactions = query.all()
    
    return transactions, total


def get_transaction(db: Session, transaction_id: int, user_id: int) -> Transaction:
    """Get a specific transaction by ID."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


def create_transaction(db: Session, user_id: int, transaction_data: TransactionCreate) -> Transaction:
    """Create a new transaction."""
    # Validate account exists and belongs to user
    account = db.query(Account).filter(
        Account.id == transaction_data.account_id,
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
            detail="Cannot create transaction for archived account"
        )
    
    # Validate category if provided
    if transaction_data.category_id:
        category = db.query(Category).filter(
            Category.id == transaction_data.category_id,
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
        if transaction_data.type == "income" and category.type != "income":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use expense category for income transaction"
            )
        
        if transaction_data.type == "expense" and category.type != "expense":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use income category for expense transaction"
            )
    
    # Validate transfer
    if transaction_data.type == "transfer":
        if not transaction_data.transfer_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer requires transfer_account_id"
            )
        
        transfer_account = db.query(Account).filter(
            Account.id == transaction_data.transfer_account_id,
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
    
    # Create transaction
    transaction = Transaction(
        user_id=user_id,
        account_id=transaction_data.account_id,
        category_id=transaction_data.category_id,
        type=transaction_data.type,
        amount=transaction_data.amount,
        date=transaction_data.date,
        note=transaction_data.note,
        reference=transaction_data.reference,
        transfer_account_id=transaction_data.transfer_account_id,
    )
    
    db.add(transaction)
    
    # Update account balances
    if transaction_data.type == "income":
        account.current_balance += transaction_data.amount
    elif transaction_data.type == "expense":
        account.current_balance -= transaction_data.amount
    elif transaction_data.type == "transfer":
        # Deduct from source account
        account.current_balance -= transaction_data.amount
        # Add to target account
        transfer_account = db.query(Account).filter(
            Account.id == transaction_data.transfer_account_id
        ).first()
        transfer_account.current_balance += transaction_data.amount
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


def update_transaction(db: Session, transaction_id: int, user_id: int, transaction_data: TransactionUpdate) -> Transaction:
    """Update a transaction."""
    transaction = get_transaction(db, transaction_id, user_id)
    
    # Store original values for balance recalculation
    original_type = transaction.type
    original_amount = transaction.amount
    original_account_id = transaction.account_id
    original_transfer_account_id = transaction.transfer_account_id
    
    update_data = transaction_data.model_dump(exclude_unset=True)
    
    # Validate updates
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
        
        transaction_type = update_data.get("type", transaction.type)
        if transaction_type == "income" and category.type != "income":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use expense category for income transaction"
            )
        
        if transaction_type == "expense" and category.type != "expense":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot use income category for expense transaction"
            )
    
    # Update fields
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    # Recalculate balances
    # First, reverse the original transaction
    if original_type == "income":
        db.query(Account).filter(Account.id == original_account_id).update(
            {Account.current_balance: Account.current_balance - original_amount}
        )
    elif original_type == "expense":
        db.query(Account).filter(Account.id == original_account_id).update(
            {Account.current_balance: Account.current_balance + original_amount}
        )
    elif original_type == "transfer" and original_transfer_account_id:
        db.query(Account).filter(Account.id == original_account_id).update(
            {Account.current_balance: Account.current_balance + original_amount}
        )
        db.query(Account).filter(Account.id == original_transfer_account_id).update(
            {Account.current_balance: Account.current_balance - original_amount}
        )
    
    # Then apply the new transaction
    current_type = transaction.type
    current_amount = transaction.amount
    current_account_id = transaction.account_id
    current_transfer_account_id = transaction.transfer_account_id
    
    if current_type == "income":
        db.query(Account).filter(Account.id == current_account_id).update(
            {Account.current_balance: Account.current_balance + current_amount}
        )
    elif current_type == "expense":
        db.query(Account).filter(Account.id == current_account_id).update(
            {Account.current_balance: Account.current_balance - current_amount}
        )
    elif current_type == "transfer" and current_transfer_account_id:
        db.query(Account).filter(Account.id == current_account_id).update(
            {Account.current_balance: Account.current_balance - current_amount}
        )
        db.query(Account).filter(Account.id == current_transfer_account_id).update(
            {Account.current_balance: Account.current_balance + current_amount}
        )
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


def delete_transaction(db: Session, transaction_id: int, user_id: int) -> None:
    """Delete a transaction and recalculate balances."""
    transaction = get_transaction(db, transaction_id, user_id)
    
    # Reverse the transaction effect on balances
    if transaction.type == "income":
        db.query(Account).filter(Account.id == transaction.account_id).update(
            {Account.current_balance: Account.current_balance - transaction.amount}
        )
    elif transaction.type == "expense":
        db.query(Account).filter(Account.id == transaction.account_id).update(
            {Account.current_balance: Account.current_balance + transaction.amount}
        )
    elif transaction.type == "transfer" and transaction.transfer_account_id:
        db.query(Account).filter(Account.id == transaction.account_id).update(
            {Account.current_balance: Account.current_balance + transaction.amount}
        )
        db.query(Account).filter(Account.id == transaction.transfer_account_id).update(
            {Account.current_balance: Account.current_balance - transaction.amount}
        )
    
    db.delete(transaction)
    db.commit()
