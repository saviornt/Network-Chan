"""Authentication domain package for Network-Chan.

Contains reusable, non-HTTP authentication logic:
- Low-level primitives (`auth.py`): hashing, JWT, TOTP utilities, password validation
- Async business logic layer (`auth_service.py`): login flow, credential changes, TOTP enable/verify, user lookup

This package does NOT contain FastAPI routers or HTTP endpoints — those live in shared/src/api/.

Public exports:
    - Useful functions/classes that other modules might need directly
    - (router is NOT exported here — import from api/ instead)

Typical usage:
    from shared.src.authentication import login_user, change_password, PasswordValidator

    # or just import specific symbols as needed
"""

from .auth import (
    hash_password,
    verify_password,
    validate_password,
    password_validator,
    create_access_token,
    decode_access_token,
    generate_totp_secret,
    verify_totp,
    get_totp_provisioning_uri,
)
from .auth_service import (
    get_user_by_username,
    create_initial_admin,
    change_password,
    enable_totp,
    verify_login,
    login_user,
)

__all__ = [
    # Low-level utils
    "hash_password",
    "verify_password",
    "validate_password",
    "password_validator",
    "create_access_token",
    "decode_access_token",
    "generate_totp_secret",
    "verify_totp",
    "get_totp_provisioning_uri",
    # Service layer
    "get_user_by_username",
    "create_initial_admin",
    "change_password",
    "enable_totp",
    "verify_login",
    "login_user",
]
