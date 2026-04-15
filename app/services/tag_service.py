"""Tag service."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.tag import Tag, transaction_tags
from app.models.transaction import Transaction
from app.schemas.tag import TagCreate, TagUpdate


def get_tags(db: Session, user_id: int, search: Optional[str] = None) -> List[Tag]:
    """Get all tags for a user."""
    query = db.query(Tag).filter(Tag.user_id == user_id)
    
    if search:
        query = query.filter(Tag.name.ilike(f"%{search}%"))
    
    return query.order_by(Tag.name.asc()).all()


def get_tag(db: Session, tag_id: int, user_id: int) -> Tag:
    """Get a specific tag by ID."""
    tag = db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.user_id == user_id
    ).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    return tag


def create_tag(db: Session, user_id: int, tag_data: TagCreate) -> Tag:
    """Create a new tag."""
    # Check for duplicate name (case-insensitive)
    existing = db.query(Tag).filter(
        Tag.user_id == user_id,
        func.lower(Tag.name) == tag_data.name.lower()
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{tag_data.name}' already exists"
        )

    tag = Tag(
        user_id=user_id,
        name=tag_data.name.lower().strip(),
        color=tag_data.color
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)

    return tag


def update_tag(db: Session, tag_id: int, user_id: int, tag_data: TagUpdate) -> Tag:
    """Update a tag."""
    tag = get_tag(db, tag_id, user_id)

    update_data = tag_data.model_dump(exclude_unset=True)

    # Check for duplicate name if name is being changed
    if "name" in update_data:
        new_name = update_data["name"].lower().strip()
        existing = db.query(Tag).filter(
            Tag.user_id == user_id,
            func.lower(Tag.name) == new_name,
            Tag.id != tag_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{new_name}' already exists"
            )

        update_data["name"] = new_name

    for field, value in update_data.items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)

    return tag


def delete_tag(db: Session, tag_id: int, user_id: int) -> None:
    """Delete a tag (removes from all transactions)."""
    tag = get_tag(db, tag_id, user_id)
    db.delete(tag)
    db.commit()


def get_tag_usage(db: Session, user_id: int) -> List[dict]:
    """Get tag usage count (how many transactions each tag is on)."""
    tags = db.query(Tag).filter(Tag.user_id == user_id).all()
    
    usage = []
    for tag in tags:
        count = (
            db.query(transaction_tags)
            .filter(transaction_tags.c.tag_id == tag.id)
            .count()
        )
        usage.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "usage_count": count
        })
    
    return sorted(usage, key=lambda x: x["usage_count"], reverse=True)
