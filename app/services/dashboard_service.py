"""Dashboard service."""

from datetime import date, timedelta
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category


def get_dashboard_summary(db: Session, user_id: int) -> dict:
    """Get dashboard summary for a user."""
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    # Total balance across all active accounts
    total_balance = db.query(func.coalesce(func.sum(Account.current_balance), 0)).filter(
        Account.user_id == user_id,
        Account.is_active == True
    ).scalar()
    
    # This month's income
    this_month_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "income",
        Transaction.date >= first_day_of_month,
        Transaction.date <= today
    ).scalar()
    
    # This month's expense
    this_month_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= first_day_of_month,
        Transaction.date <= today
    ).scalar()
    
    # This month's savings
    this_month_savings = this_month_income - this_month_expense
    
    # Recent 10 transactions
    recent_transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(
        Transaction.date.desc(), Transaction.created_at.desc()
    ).limit(10).all()
    
    # Expense by category this month
    expense_by_category = db.query(
        Category.id,
        Category.name,
        func.coalesce(func.sum(Transaction.amount), 0).label("total")
    ).outerjoin(
        Transaction,
        and_(
            Transaction.category_id == Category.id,
            Transaction.type == "expense",
            Transaction.date >= first_day_of_month,
            Transaction.date <= today
        )
    ).filter(
        Category.user_id == user_id,
        Category.type == "expense",
        Category.is_active == True
    ).group_by(
        Category.id, Category.name
    ).all()
    
    # Account balances
    account_balances = db.query(Account).filter(
        Account.user_id == user_id
    ).order_by(Account.name).all()
    
    return {
        "total_balance": total_balance,
        "this_month_income": this_month_income,
        "this_month_expense": this_month_expense,
        "this_month_savings": this_month_savings,
        "recent_transactions": [
            {
                "id": t.id,
                "type": t.type,
                "amount": t.amount,
                "date": t.date,
                "note": t.note,
                "account_id": t.account_id,
                "category_id": t.category_id,
            }
            for t in recent_transactions
        ],
        "expense_by_category": [
            {
                "category_id": cat[0],
                "category_name": cat[1],
                "total": cat[2]
            }
            for cat in expense_by_category
        ],
        "account_balances": [
            {
                "id": acc.id,
                "name": acc.name,
                "type": acc.type,
                "current_balance": acc.current_balance,
                "is_active": acc.is_active
            }
            for acc in account_balances
        ]
    }
