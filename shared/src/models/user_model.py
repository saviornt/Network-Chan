from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: Optional[EmailStr] = Field(
        None, description="Optional email for notifications"
    )
    role: Literal["viewer", "operator", "admin"] = Field(default="viewer")


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=12, description="Plaintext password (will be hashed)"
    )


class UserUpdate(BaseModel):
    """Fields allowed when updating an existing user (partial)."""

    email: Optional[EmailStr] = None
    role: Optional[Literal["viewer", "operator", "admin"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(
        None, min_length=12, description="New plaintext password (if changing)"
    )


class UserInDB(UserBase):
    """Full user record as stored/retrieved from the database."""

    id: Optional[UUID] = Field(None, description="Auto-generated unique UUID on insert")
    hashed_password: str
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    """Safe, public-facing user info (no secrets, no password)."""

    id: UUID
    totp_enabled: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
