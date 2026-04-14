"""Loan database model (Udhar Khata)."""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="RESTRICT"), nullable=False, index=True)

    direction = Column(String(20), nullable=False, index=True)  # lent | borrowed
    status = Column(String(20), nullable=False, server_default="open", index=True)  # open | closed

    title = Column(String(120), nullable=True)
    currency = Column(String(10), nullable=False, server_default="USD")
    interest_rate = Column(Numeric(7, 4), nullable=True)
    start_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", backref="loans")
    contact = relationship("Contact", back_populates="loans")
    entries = relationship(
        "LoanEntry",
        back_populates="loan",
        cascade="all, delete-orphan",
        order_by="LoanEntry.occurred_at",
    )
