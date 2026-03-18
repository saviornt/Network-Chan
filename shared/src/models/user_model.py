from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    is_admin: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=12)


class UserInDB(UserBase):
    """
    Full user record as stored in the database.
    """

    id: Optional[int] = Field(
        default=None,
        description="Auto-incremented primary key (assigned by DB)",
    )
    hashed_password: str
    totp_secret: Optional[str] = None  # encrypted base32 secret
    totp_enabled: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None


class User(UserBase):
    """
    Public user info (no secrets)
    """

    id: int
    totp_enabled: bool
