"""Goals (savings targets) API routes."""

from typing import List

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalProgressResponse,
    GoalDetailResponse,
    GoalContributionCreate,
    GoalContributionResponse,
)
from app.services import goal_service


router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/", response_model=List[GoalProgressResponse])
def list_goals(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return goal_service.get_goals_with_progress(db, current_user.id, include_inactive=include_inactive)


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return goal_service.create_goal(db, current_user.id, goal_data)


@router.get("/{goal_id}", response_model=GoalDetailResponse)
def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    progress_row = goal_service.get_goal_with_progress(db, goal_id, current_user.id)
    contributions = goal_service.list_goal_contributions(db, goal_id, current_user.id)
    return {**progress_row, "contributions": contributions}


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return goal_service.update_goal(db, goal_id, current_user.id, goal_data)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    goal_service.delete_goal(db, goal_id, current_user.id)
    return None


@router.get("/{goal_id}/contributions", response_model=List[GoalContributionResponse])
def list_contributions(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return goal_service.list_goal_contributions(db, goal_id, current_user.id)


@router.post("/{goal_id}/contributions", response_model=GoalContributionResponse, status_code=status.HTTP_201_CREATED)
def add_contribution(
    goal_id: int,
    contribution_data: GoalContributionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return goal_service.add_goal_contribution(db, goal_id, current_user.id, contribution_data)


@router.delete("/{goal_id}/contributions/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contribution(
    goal_id: int,
    contribution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    goal_service.delete_goal_contribution(db, goal_id, contribution_id, current_user.id)
    return None
