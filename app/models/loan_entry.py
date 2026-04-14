"""Loan entry database model (disbursements/repayments)."""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class LoanEntry(Base):
    __tablename__ = "loan_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)

    kind = Column(String(20), nullable=False, index=True)  # disbursement | repayment
    amount = Column(Numeric(15, 2), nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="loan_entries")
    loan = relationship("Loan", back_populates="entries")

