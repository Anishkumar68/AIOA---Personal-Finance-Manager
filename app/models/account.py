"""Account database model."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # cash, bank, wallet, credit_card
    currency = Column(String(10), nullable=False, default="USD")
    opening_balance = Column(Numeric(15, 2), nullable=False, default=0)
    current_balance = Column(Numeric(15, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="accounts")
    transactions = relationship("Transaction", back_populates="account", foreign_keys="Transaction.account_id")
    transfer_transactions = relationship("Transaction", foreign_keys="Transaction.transfer_account_id")
