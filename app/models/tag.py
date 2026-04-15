"""Tag database model."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# Many-to-many association table
transaction_tags = Table(
    "transaction_tags",
    Base.metadata,
    Column("transaction_id", Integer, ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)  # e.g. "vacation", "office", "subscription"
    color = Column(String(7), nullable=True)  # hex color, e.g. "#4f46e5"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="tags")
    transactions = relationship(
        "Transaction",
        secondary=transaction_tags,
        back_populates="tags",
        overlaps="transaction_tags_rel"
    )
