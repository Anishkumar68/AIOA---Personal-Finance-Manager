"""Reports API routes."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly-summary", response_model=dict)
def get_monthly_summary(
    month: date = Query(..., description="Month to get summary for (YYYY-MM-DD format, use first day of month)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get monthly summary report."""
    return report_service.get_monthly_summary(db, current_user.id, month)


@router.get("/category-expense", response_model=dict)
def get_category_expense_report(
    month: date = Query(..., description="Month to get report for (YYYY-MM-DD format, use first day of month)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get category expense report."""
    return report_service.get_category_expense_report(db, current_user.id, month)


@router.get("/account-balances", response_model=dict)
def get_account_balances_report(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account balances report."""
    return report_service.get_account_balances_report(db, current_user.id)


@router.get("/cashflow-series", response_model=dict)
def get_cashflow_series(
    from_date: date = Query(...),
    to_date: date = Query(...),
    bucket: Literal["day", "month"] = Query("day"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cashflow time series for charts (income/expense/net)."""
    return report_service.get_cashflow_series(db, current_user.id, from_date, to_date, bucket=bucket)
