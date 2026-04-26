"""Authentication schemas."""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


def validate_bcrypt_password_length(password: str) -> str:
    """Bcrypt accepts at most 72 UTF-8 bytes, not 72 characters."""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password cannot be longer than 72 bytes")
    return password


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)

    _validate_password_bytes = field_validator("password")(validate_bcrypt_password_length)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)

    _validate_password_bytes = field_validator("password")(validate_bcrypt_password_length)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None  # returned only in DEBUG for local testing


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=200)
    new_password: str = Field(..., min_length=6, max_length=72)

    _validate_password_bytes = field_validator("new_password")(validate_bcrypt_password_length)


class ResetPasswordResponse(BaseModel):
    message: str
