"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.services import auth_service
from app.services.category_service import seed_default_categories

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    user = auth_service.register_user(db, user_data)

    # Seed default categories
    seed_default_categories(db, user.id)

    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access and refresh tokens."""
    result = auth_service.login_user(db, login_data)

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.post("/refresh", response_model=dict)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Refresh access token."""
    return auth_service.refresh_access_token(db, refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset token.

    Always returns a success message to avoid user enumeration. In DEBUG, returns the reset token.
    """
    token = auth_service.create_password_reset_token(db, body.email)
    resp = {"message": "If an account exists for this email, a reset token has been generated."}
    if settings.DEBUG and token:
        resp["reset_token"] = token
    return resp


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    auth_service.reset_password_with_token(db, body.token, body.new_password)
    return {"message": "Password has been reset successfully."}
