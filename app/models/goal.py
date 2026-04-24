"""Goal (savings target) database models."""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(120), nullable=False, index=True)
    currency = Column(String(3), nullable=False, default="INR")
    target_amount = Column(Numeric(15, 2), nullable=False)

    start_date = Column(Date, nullable=False, index=True)
    target_date = Column(Date, nullable=True, index=True)
    note = Column(String(500), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", backref="goals")
    contributions = relationship(
        "GoalContribution",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by=lambda: (GoalContribution.date.desc(), GoalContribution.id.desc()),
    )


class GoalContribution(Base):
    __tablename__ = "goal_contributions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)

    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    note = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="goal_contributions")
    goal = relationship("Goal", back_populates="contributions")
