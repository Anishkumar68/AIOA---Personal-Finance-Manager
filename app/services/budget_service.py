"""Budget service."""

from typing import List
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate, BudgetUpdate


def get_budgets(db: Session, user_id: int, month: date = None) -> List[Budget]:
    """Get all budgets for a user."""
    query = db.query(Budget).filter(Budget.user_id == user_id)
    
    if month:
        # Get budgets for specific month
        first_day = month.replace(day=1)
        query = query.filter(Budget.month == first_day)
    
    return query.all()


def get_budget(db: Session, budget_id: int, user_id: int) -> Budget:
    """Get a specific budget by ID."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    return budget


def create_budget(db: Session, user_id: int, budget_data: BudgetCreate) -> Budget:
    """Create a new budget."""
    # Validate category
    category = db.query(Category).filter(
        Category.id == budget_data.category_id,
        Category.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if budget already exists for this category and month
    first_day = budget_data.month.replace(day=1)
    existing_budget = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == budget_data.category_id,
        Budget.month == first_day
    ).first()
    
    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget already exists for this category and month"
        )
    
    budget = Budget(
        user_id=user_id,
        category_id=budget_data.category_id,
        month=first_day,
        amount=budget_data.amount
    )
    
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    return budget


def update_budget(db: Session, budget_id: int, user_id: int, budget_data: BudgetUpdate) -> Budget:
    """Update a budget."""
    budget = get_budget(db, budget_id, user_id)
    
    budget.amount = budget_data.amount
    
    db.commit()
    db.refresh(budget)
    
    return budget


def delete_budget(db: Session, budget_id: int, user_id: int) -> None:
    """Delete a budget."""
    budget = get_budget(db, budget_id, user_id)
    
    db.delete(budget)
    db.commit()


def get_budget_progress(db: Session, user_id: int, month: date = None) -> List[dict]:
    """Get budget progress for a month."""
    if not month:
        month = date.today()
    
    first_day = month.replace(day=1)
    if month.month == 12:
        last_day = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = month.replace(month=month.month + 1, day=1) - timedelta(days=1)
    
    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.month == first_day
    ).all()
    
    result = []
    for budget in budgets:
        # Calculate spent
        spent = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == budget.category_id,
            Transaction.type == "expense",
            Transaction.date >= first_day,
            Transaction.date <= last_day
        ).scalar()
        
        remaining = budget.amount - spent
        overspent = spent > budget.amount
        
        result.append({
            "budget_id": budget.id,
            "category_id": budget.category_id,
            "category_name": budget.category.name,
            "limit_amount": budget.amount,
            "spent_amount": spent,
            "remaining_amount": remaining,
            "overspent": overspent
        })
    
    return result
