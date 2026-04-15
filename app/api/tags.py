"""Tag API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.services import tag_service as service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=dict)
def get_tags(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all tags for the current user."""
    tags = service.get_tags(db, current_user.id, search)
    
    return {
        "items": tags,
        "total": len(tags)
    }


@router.get("/usage")
def get_tag_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get tag usage statistics."""
    return service.get_tag_usage(db, current_user.id)


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new tag."""
    return service.create_tag(db, current_user.id, tag_data)


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific tag."""
    return service.get_tag(db, tag_id, current_user.id)


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a tag."""
    return service.update_tag(db, tag_id, current_user.id, tag_data)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a tag (removes from all transactions)."""
    service.delete_tag(db, tag_id, current_user.id)
    return None
