"""Reports service."""

from typing import List, Literal
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category


def get_monthly_summary(db: Session, user_id: int, month: date) -> dict:
    """Get monthly summary report."""
    first_day = month.replace(day=1)
    if month.month == 12:
        last_day = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = month.replace(month=month.month + 1, day=1) - timedelta(days=1)
    
    # Total income
    total_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "income",
        Transaction.date >= first_day,
        Transaction.date <= last_day
    ).scalar()
    
    # Total expense
    total_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= first_day,
        Transaction.date <= last_day
    ).scalar()
    
    # Net savings
    net_savings = total_income - total_expense
    
    return {
        "month": first_day,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_savings": net_savings
    }


def get_category_expense_report(db: Session, user_id: int, month: date) -> dict:
    """Get category expense report."""
    first_day = month.replace(day=1)
    if month.month == 12:
        last_day = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = month.replace(month=month.month + 1, day=1) - timedelta(days=1)
    
    # Get expenses by category
    category_expenses = db.query(
        Category.id,
        Category.name,
        func.coalesce(func.sum(Transaction.amount), 0).label("total_spent"),
        func.count(Transaction.id).label("transaction_count")
    ).outerjoin(
        Transaction,
        and_(
            Transaction.category_id == Category.id,
            Transaction.type == "expense",
            Transaction.date >= first_day,
            Transaction.date <= last_day
        )
    ).filter(
        Category.user_id == user_id,
        Category.type == "expense"
    ).group_by(
        Category.id, Category.name
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()
    
    categories = [
        {
            "category_id": cat[0],
            "category_name": cat[1],
            "total_spent": cat[2],
            "transaction_count": cat[3]
        }
        for cat in category_expenses
    ]
    
    return {
        "month": first_day,
        "categories": categories
    }


def get_account_balances_report(db: Session, user_id: int) -> dict:
    """Get account balances report."""
    accounts = db.query(Account).filter(
        Account.user_id == user_id
    ).order_by(Account.name).all()
    
    account_data = []
    for account in accounts:
        # Count transactions
        transaction_count = db.query(func.count(Transaction.id)).filter(
            Transaction.account_id == account.id
        ).scalar()
        
        # Total income
        total_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "income"
        ).scalar()
        
        # Total expense
        total_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.account_id == account.id,
            Transaction.type == "expense"
        ).scalar()
        
        account_data.append({
            "account_id": account.id,
            "account_name": account.name,
            "account_type": account.type,
            "opening_balance": account.opening_balance,
            "current_balance": account.current_balance,
            "is_active": account.is_active,
            "transaction_count": transaction_count,
            "total_income": total_income,
            "total_expense": total_expense
        })
    
    return {
        "accounts": account_data
    }


def get_cashflow_series(
    db: Session,
    user_id: int,
    from_date: date,
    to_date: date,
    bucket: Literal["day", "month"] = "day",
) -> dict:
    """Return an income/expense/net time series for charts."""
    if to_date < from_date:
        return {"from_date": from_date, "to_date": to_date, "bucket": bucket, "series": []}

    txns = (
        db.query(Transaction.date, Transaction.type, Transaction.amount)
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.type.in_(["income", "expense"]),
        )
        .all()
    )

    series_map: dict[date, dict[str, Decimal]] = {}

    def bucket_key(d: date) -> date:
        if bucket == "month":
            return d.replace(day=1)
        return d

    for d, t, amt in txns:
        key = bucket_key(d)
        row = series_map.get(key)
        if not row:
            row = {"income": Decimal("0"), "expense": Decimal("0")}
            series_map[key] = row
        if t == "income":
            row["income"] += Decimal(amt)
        elif t == "expense":
            row["expense"] += Decimal(amt)

    def iter_periods() -> List[date]:
        if bucket == "month":
            cur = from_date.replace(day=1)
            end = to_date.replace(day=1)
            out: List[date] = []
            while cur <= end:
                out.append(cur)
                if cur.month == 12:
                    cur = cur.replace(year=cur.year + 1, month=1, day=1)
                else:
                    cur = cur.replace(month=cur.month + 1, day=1)
            return out

        # day bucket
        out: List[date] = []
        cur = from_date
        while cur <= to_date:
            out.append(cur)
            cur = cur + timedelta(days=1)
        return out

    series = []
    for key in iter_periods():
        row = series_map.get(key) or {"income": Decimal("0"), "expense": Decimal("0")}
        income = row["income"]
        expense = row["expense"]
        series.append({"period": key, "income": income, "expense": expense, "net": income - expense})

    total_income = sum((s["income"] for s in series), Decimal("0"))
    total_expense = sum((s["expense"] for s in series), Decimal("0"))

    return {
        "from_date": from_date,
        "to_date": to_date,
        "bucket": bucket,
        "total_income": total_income,
        "total_expense": total_expense,
        "net": total_income - total_expense,
        "series": series,
    }
