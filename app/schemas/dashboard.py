"""Dashboard and Report schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal


class DashboardSummary(BaseModel):
    total_balance: Decimal
    this_month_income: Decimal
    this_month_expense: Decimal
    this_month_savings: Decimal
    recent_transactions: List[dict]
    expense_by_category: List[dict]
    account_balances: List[dict]


class MonthlySummary(BaseModel):
    month: date
    total_income: Decimal
    total_expense: Decimal
    net_savings: Decimal


class CategoryExpense(BaseModel):
    category_id: int
    category_name: str
    total_spent: Decimal


class CategoryExpenseReport(BaseModel):
    month: date
    categories: List[CategoryExpense]


class AccountBalance(BaseModel):
    account_id: int
    account_name: str
    account_type: str
    current_balance: Decimal
