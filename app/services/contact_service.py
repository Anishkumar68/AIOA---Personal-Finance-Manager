"""Contact service."""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate


def list_contacts(db: Session, user_id: int, include_inactive: bool = False) -> List[Contact]:
    query = db.query(Contact).filter(Contact.user_id == user_id)
    if not include_inactive:
        query = query.filter(Contact.is_active.is_(True))
    return query.order_by(Contact.name.asc()).all()


def get_contact(db: Session, contact_id: int, user_id: int) -> Contact:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


def create_contact(db: Session, user_id: int, payload: ContactCreate) -> Contact:
    contact = Contact(user_id=user_id, name=payload.name, phone=payload.phone, notes=payload.notes)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db: Session, contact_id: int, user_id: int, payload: ContactUpdate) -> Contact:
    contact = get_contact(db, contact_id, user_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


def archive_contact(db: Session, contact_id: int, user_id: int) -> None:
    contact = get_contact(db, contact_id, user_id)
    contact.is_active = False
    db.commit()

