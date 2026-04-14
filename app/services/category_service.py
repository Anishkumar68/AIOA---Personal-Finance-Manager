"""Category service."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_categories(db: Session, user_id: int, category_type: str = None, include_inactive: bool = False) -> List[Category]:
    """Get all categories for a user."""
    query = db.query(Category).filter(Category.user_id == user_id)
    
    if category_type:
        query = query.filter(Category.type == category_type)
    
    if not include_inactive:
        query = query.filter(Category.is_active == True)
    
    return query.all()


def get_category(db: Session, category_id: int, user_id: int) -> Category:
    """Get a specific category by ID."""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


def create_category(db: Session, user_id: int, category_data: CategoryCreate) -> Category:
    """Create a new category."""
    category = Category(
        user_id=user_id,
        name=category_data.name,
        type=category_data.type,
        is_active=True
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


def update_category(db: Session, category_id: int, user_id: int, category_data: CategoryUpdate) -> Category:
    """Update a category."""
    category = get_category(db, category_id, user_id)
    
    update_data = category_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    return category


def delete_category(db: Session, category_id: int, user_id: int) -> None:
    """Delete a category (only if unused)."""
    category = get_category(db, category_id, user_id)
    
    # Check if category is used in transactions
    transaction_count = db.query(func.count(Transaction.id)).filter(
        Transaction.category_id == category_id
    ).scalar()
    
    if transaction_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category that has transactions"
        )
    
    db.delete(category)
    db.commit()


def seed_default_categories(db: Session, user_id: int) -> None:
    """Seed default categories for a new user."""
    default_categories = [
        # Income categories
        {"name": "Salary", "type": "income"},
        {"name": "Freelance", "type": "income"},
        {"name": "Investment", "type": "income"},
        {"name": "Gift", "type": "income"},
        {"name": "Other Income", "type": "income"},
        
        # Expense categories
        {"name": "Food", "type": "expense"},
        {"name": "Rent", "type": "expense"},
        {"name": "Transport", "type": "expense"},
        {"name": "Shopping", "type": "expense"},
        {"name": "Health", "type": "expense"},
        {"name": "Entertainment", "type": "expense"},
        {"name": "Utilities", "type": "expense"},
        {"name": "Education", "type": "expense"},
        {"name": "Travel", "type": "expense"},
        {"name": "Other Expense", "type": "expense"},
    ]
    
    for cat_data in default_categories:
        # Check if category already exists
        existing = db.query(Category).filter(
            Category.user_id == user_id,
            Category.name == cat_data["name"],
            Category.type == cat_data["type"]
        ).first()
        
        if not existing:
            category = Category(
                user_id=user_id,
                name=cat_data["name"],
                type=cat_data["type"],
                is_active=True
            )
            db.add(category)
    
    db.commit()
