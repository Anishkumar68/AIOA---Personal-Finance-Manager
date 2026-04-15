"""Transaction database model."""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # income, expense, transfer
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    note = Column(String(500), nullable=True)
    reference = Column(String(100), nullable=True)
    transfer_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="transactions")
    account = relationship("Account", back_populates="transactions", foreign_keys=[account_id])
    category = relationship("Category", back_populates="transactions", foreign_keys=[category_id])
    transfer_account = relationship("Account", foreign_keys=[transfer_account_id], overlaps="transfer_transactions")
    tags = relationship(
        "Tag",
        secondary="transaction_tags",
        back_populates="transactions",
        overlaps="transaction_tags_rel"
    )
