"""Seed script to populate database with initial data."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.category import Category
from app.services.category_service import seed_default_categories
from app.core.security import get_password_hash


def seed_database():
    """Seed the database with initial data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if users exist
        existing_user = db.query(User).first()
        
        if not existing_user:
            print("Creating demo user...")
            demo_user = User(
                name="Demo User",
                email="demo@example.com",
                password_hash=get_password_hash("demopassword"),
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print(f"Created demo user with ID: {demo_user.id}")
            
            # Seed categories for demo user
            seed_default_categories(db, demo_user.id)
            print(f"Seeded default categories for demo user")
        else:
            print(f"User already exists: {existing_user.email}")
            # Seed categories if they don't exist
            categories_count = db.query(Category).filter(Category.user_id == existing_user.id).count()
            if categories_count == 0:
                seed_default_categories(db, existing_user.id)
                print(f"Seeded default categories for existing user")
            else:
                print(f"Categories already exist for user")
        
        print("\nSeed completed successfully!")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
