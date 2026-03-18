from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from passlib.context import CryptContext  # or bcrypt

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    is_admin: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=12)


class UserInDB(UserBase):
    id: int
    hashed_password: str
    totp_secret: Optional[str] = None  # encrypted base32 secret
    totp_enabled: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None


class User(UserBase):
    """Public user info (no secrets)"""

    id: int
    totp_enabled: bool


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
