"""Authentication Request and Response Pydantic Schemas."""

from datetime import datetime
import re
import uuid
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for student registration."""

    email: EmailStr = Field(..., description="Student's valid email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Strong password"
    )
    full_name: str = Field(
        ..., min_length=2, max_length=100, description="Student's full name"
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = re.sub(r"\s+", " ", v.strip())
            return cleaned
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError(
                "Password must be at least 8 characters long and contain both letters and numbers"
            )
        return v


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    email: EmailStr = Field(..., description="Registered account email")
    password: str = Field(..., description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserResponse(BaseModel):
    """Public user identity contract."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    roles: List[str]
    onboarding_completed: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Authenticated session token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse
