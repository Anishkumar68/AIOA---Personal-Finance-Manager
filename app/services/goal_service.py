"""Goal (savings target) service."""

from __future__ import annotations

from datetime import date as date_type
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.goal import Goal, GoalContribution
from app.schemas.goal import GoalCreate, GoalUpdate, GoalContributionCreate


def _validate_dates(start_date: date_type, target_date: Optional[date_type]) -> None:
    if target_date and target_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_date cannot be before start_date",
        )


def get_goal(db: Session, goal_id: int, user_id: int) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


def create_goal(db: Session, user_id: int, goal_data: GoalCreate) -> Goal:
    _validate_dates(goal_data.start_date, goal_data.target_date)

    goal = Goal(
        user_id=user_id,
        name=goal_data.name.strip(),
        currency=goal_data.currency.upper(),
        target_amount=goal_data.target_amount,
        start_date=goal_data.start_date,
        target_date=goal_data.target_date,
        note=goal_data.note,
        is_active=True,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal_id: int, user_id: int, goal_data: GoalUpdate) -> Goal:
    goal = get_goal(db, goal_id, user_id)

    start_date = goal_data.start_date if goal_data.start_date is not None else goal.start_date
    target_date = goal_data.target_date if goal_data.target_date is not None else goal.target_date
    _validate_dates(start_date, target_date)

    if goal_data.name is not None:
        goal.name = goal_data.name.strip()
    if goal_data.currency is not None:
        goal.currency = goal_data.currency.upper()
    if goal_data.target_amount is not None:
        goal.target_amount = goal_data.target_amount
    if goal_data.start_date is not None:
        goal.start_date = goal_data.start_date
    if goal_data.target_date is not None:
        goal.target_date = goal_data.target_date
    if goal_data.note is not None:
        goal.note = goal_data.note
    if goal_data.is_active is not None:
        goal.is_active = goal_data.is_active

    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal_id: int, user_id: int) -> None:
    goal = get_goal(db, goal_id, user_id)
    db.delete(goal)
    db.commit()


def get_goals_with_progress(
    db: Session,
    user_id: int,
    include_inactive: bool = False,
) -> List[dict]:
    saved_subq = (
        db.query(
            GoalContribution.goal_id.label("goal_id"),
            func.coalesce(func.sum(GoalContribution.amount), 0).label("saved_amount"),
            func.count(GoalContribution.id).label("contributions_count"),
        )
        .filter(GoalContribution.user_id == user_id)
        .group_by(GoalContribution.goal_id)
        .subquery()
    )

    query = (
        db.query(
            Goal,
            func.coalesce(saved_subq.c.saved_amount, 0).label("saved_amount"),
            func.coalesce(saved_subq.c.contributions_count, 0).label("contributions_count"),
        )
        .outerjoin(saved_subq, Goal.id == saved_subq.c.goal_id)
        .filter(Goal.user_id == user_id)
        .order_by(Goal.created_at.desc(), Goal.id.desc())
    )

    if not include_inactive:
        query = query.filter(Goal.is_active == True)  # noqa: E712

    rows: List[Tuple[Goal, Decimal, int]] = query.all()
    result: List[dict] = []
    for goal, saved_amount, contributions_count in rows:
        target = Decimal(goal.target_amount or 0)
        saved = Decimal(saved_amount or 0)
        remaining = target - saved
        if remaining < 0:
            remaining = Decimal("0")

        pct = 0.0
        if target > 0:
            pct = float((saved / target) * Decimal("100"))
            pct = max(0.0, min(100.0, pct))

        result.append(
            {
                "id": goal.id,
                "user_id": goal.user_id,
                "name": goal.name,
                "currency": goal.currency,
                "target_amount": goal.target_amount,
                "start_date": goal.start_date,
                "target_date": goal.target_date,
                "note": goal.note,
                "is_active": goal.is_active,
                "created_at": goal.created_at,
                "updated_at": goal.updated_at,
                "saved_amount": saved,
                "remaining_amount": remaining,
                "progress_pct": pct,
                "is_completed": saved >= target and target > 0,
                "contributions_count": int(contributions_count or 0),
            }
        )

    return result


def get_goal_with_progress(db: Session, goal_id: int, user_id: int) -> dict:
    goal = get_goal(db, goal_id, user_id)
    saved_amount = (
        db.query(func.coalesce(func.sum(GoalContribution.amount), 0))
        .filter(GoalContribution.user_id == user_id, GoalContribution.goal_id == goal_id)
        .scalar()
    )
    contributions_count = (
        db.query(func.count(GoalContribution.id))
        .filter(GoalContribution.user_id == user_id, GoalContribution.goal_id == goal_id)
        .scalar()
    )

    target = Decimal(goal.target_amount or 0)
    saved = Decimal(saved_amount or 0)
    remaining = target - saved
    if remaining < 0:
        remaining = Decimal("0")

    pct = 0.0
    if target > 0:
        pct = float((saved / target) * Decimal("100"))
        pct = max(0.0, min(100.0, pct))

    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "currency": goal.currency,
        "target_amount": goal.target_amount,
        "start_date": goal.start_date,
        "target_date": goal.target_date,
        "note": goal.note,
        "is_active": goal.is_active,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "saved_amount": saved,
        "remaining_amount": remaining,
        "progress_pct": pct,
        "is_completed": saved >= target and target > 0,
        "contributions_count": int(contributions_count or 0),
    }


def list_goal_contributions(db: Session, goal_id: int, user_id: int) -> List[GoalContribution]:
    _ = get_goal(db, goal_id, user_id)
    return (
        db.query(GoalContribution)
        .filter(GoalContribution.goal_id == goal_id, GoalContribution.user_id == user_id)
        .order_by(GoalContribution.date.desc(), GoalContribution.id.desc())
        .all()
    )


def add_goal_contribution(
    db: Session,
    goal_id: int,
    user_id: int,
    contribution_data: GoalContributionCreate,
) -> GoalContribution:
    goal = get_goal(db, goal_id, user_id)
    if not goal.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Goal is archived")

    occurred = contribution_data.date or date_type.today()
    if occurred < goal.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contribution date cannot be before goal start_date",
        )

    contribution = GoalContribution(
        user_id=user_id,
        goal_id=goal_id,
        amount=contribution_data.amount,
        date=occurred,
        note=contribution_data.note,
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution


def delete_goal_contribution(db: Session, goal_id: int, contribution_id: int, user_id: int) -> None:
    _ = get_goal(db, goal_id, user_id)
    contribution = (
        db.query(GoalContribution)
        .filter(
            GoalContribution.id == contribution_id,
            GoalContribution.goal_id == goal_id,
            GoalContribution.user_id == user_id,
        )
        .first()
    )
    if not contribution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")
    db.delete(contribution)
    db.commit()
