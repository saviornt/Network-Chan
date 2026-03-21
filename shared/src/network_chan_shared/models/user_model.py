"""Pydantic model and SQLAlchemy ORM schema definitions for the User entity."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .sqlite_models import Base  # After modular refactor; currently from sqlite_models


# ────────────────────────────────────────────────
# Pydantic base – shared fields & configuration
# ────────────────────────────────────────────────
class UserBase(BaseModel):
    """Common fields and configuration shared across all User-related schemas."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="Unique username used for authentication",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Optional email address for recovery and notifications",
    )
    alias: Optional[str] = Field(
        None,
        min_length=3,
        max_length=32,
        description="Optional display/alternative name for the user",
    )
    role: Literal["viewer", "operator", "admin"] = Field(
        default="viewer",
        description="Role-based access control level",
    )

    model_config = ConfigDict(
        from_attributes=True,  # Allows .model_validate() on ORM objects
        populate_by_name=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "username": "dave",
                    "email": "dave@example.com",
                    "alias": "DaveTheBuilder",
                }
            ]
        },
    )


# ────────────────────────────────────────────────
# Input & output DTOs (inherit from UserBase)
# ────────────────────────────────────────────────
class UserCreate(UserBase):
    """Schema used when creating a new user (includes plaintext password)."""

    password: str = Field(
        ...,
        min_length=12,
        description="Plaintext password – will be hashed before storage",
    )


class UserUpdate(UserBase):
    """Schema for partial user profile updates – only safe, user-editable fields."""

    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address (will require verification if changed)",
    )
    alias: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=32,
        description="Update display/alternative name",
    )
    password: Optional[str] = Field(
        default=None,
        min_length=12,
        description="New plaintext password – will be hashed",
    )


class UserProfileRead(UserBase):
    """Schema returned to the user on their own 'Settings' / profile page.

    Contains only information the user should see about themselves + editable fields.
    """

    id: UUID = Field(..., description="Your unique user ID")
    username: str = Field(..., description="Your login username (cannot be changed)")
    email: Optional[EmailStr] = Field(..., description="Your registered email")
    alias: Optional[str] = Field(..., description="Your display name")
    totp_enabled: bool = Field(..., description="Whether 2FA is active")
    last_login: Optional[datetime] = Field(..., description="Time of your last login")
    created_at: datetime = Field(..., description="When your account was created")


class UserAdminRead(UserProfileRead):
    """Extended read schema for admin views (all users, more metadata)."""

    is_active: bool = Field(..., description="Account active status")
    updated_at: datetime = Field(..., description="Last profile update")
    # Optional: add login_count, failed_attempts, etc. later


class UserRecord(UserBase):
    """Full internal database representation – includes secrets (never exposed externally)."""

    id: UUID
    hashed_password: str
    totp_secret: Optional[str] = Field(default=None)
    totp_enabled: bool = Field(default=False)
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(None)
    created_at: datetime
    updated_at: datetime


# ────────────────────────────────────────────────
# SQLAlchemy ORM model – database persistence layer
# ────────────────────────────────────────────────
class UserMapping(Base):
    """Persistent user accounts with role-based access control and optional TOTP 2FA."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Auto-generated UUID primary key",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for authentication",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Email address for recovery and notifications",
    )
    alias: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Optional display or alternative name for the user",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Argon2id hashed password – never store plaintext",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="viewer",
        doc="RBAC role: viewer, operator, admin",
    )
    totp_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Encrypted base32 TOTP secret (when 2FA is enabled)",
    )
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether two-factor authentication is active",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Account enabled/disabled status",
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent successful login",
    )

    __table_args__ = (
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_alias", "alias"),
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role={self.role} active={self.is_active}>"


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserProfileRead",
    "UserRecord",
    "UserMapping",
]
