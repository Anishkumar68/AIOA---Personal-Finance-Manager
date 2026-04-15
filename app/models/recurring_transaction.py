"""Recurring Transaction database model."""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # income, expense, transfer
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Recurrence settings
    frequency = Column(String(50), nullable=False)  # daily, weekly, monthly, yearly
    interval = Column(Integer, nullable=False, default=1)  # every X frequency
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # None = indefinite
    next_occurrence = Column(Date, nullable=False, index=True)  # next due date
    
    # Transaction details
    note = Column(String(500), nullable=True)
    reference = Column(String(100), nullable=True)
    transfer_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    last_processed = Column(DateTime(timezone=True), nullable=True)  # when last transaction was created
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="recurring_transactions")
    account = relationship("Account", back_populates="recurring_transactions", foreign_keys=[account_id])
    category = relationship("Category", back_populates="recurring_transactions", foreign_keys=[category_id])
    transfer_account = relationship("Account", foreign_keys=[transfer_account_id])
