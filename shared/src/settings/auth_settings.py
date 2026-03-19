"""Dedicated Pydantic Settings for authentication in Network-Chan.

Handles JWT token secrets, expiration, algorithm, and TOTP (2FA) parameters.
Environment variables are prefixed with AUTH__ (double underscore).

Example:
    export AUTH__JWT_SECRET=super-long-random-string-here
    export AUTH__TOTP_ISSUER=Network-Chan
"""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """
    Authentication configuration for JWT sessions and TOTP two-factor authentication.

    All sensitive values use SecretStr. Environment variables use AUTH__ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="AUTH__",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    # Initial / recovery credentials (only used before first password change)
    default_admin_username: str = Field(
        default="admin",
        description="Fallback username for first login",
    )
    default_admin_password_hash: str = Field(
        default="",  # Set in .env or generate on first run
        description="bcrypt/argon2 hash of initial password",
    )

    # ──────────────────────────────────────────────────────────────────────────────
    # JWT (session / API tokens)
    # ──────────────────────────────────────────────────────────────────────────────
    jwt_secret: SecretStr = Field(
        default=...,
        min_length=32,
        description=(
            "Secret key used to sign and verify JWT tokens. "
            "Should be a long, random string (at least 32 characters)."
        ),
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm (HS256, HS384, HS512, RS256, etc.).",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Lifetime of access tokens in minutes (short-lived recommended).",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Lifetime of refresh tokens in days (if refresh tokens are used).",
    )

    # ──────────────────────────────────────────────────────────────────────────────
    # TOTP (two-factor authentication)
    # ──────────────────────────────────────────────────────────────────────────────
    totp_issuer: str = Field(
        default="Network-Chan",
        description="Issuer name displayed in authenticator apps (e.g. Google Authenticator).",
    )
    totp_digits: int = Field(
        default=6,
        ge=6,
        le=8,
        description="Number of digits in each TOTP code.",
    )
    totp_interval_seconds: int = Field(
        default=30,
        ge=15,
        le=60,
        description="Time step / validity window for TOTP codes (seconds).",
    )

    # Optional: initial admin TOTP secret (only used during first setup / recovery)
    admin_initial_totp_secret: SecretStr | None = Field(
        default=None,
        description=(
            "Initial TOTP secret for admin user. Set only once during setup, "
            "then store encrypted in database. Leave empty after initial configuration."
        ),
    )

    # ──────────────────────────────────────────────────────────────────────────────
    # Password Hashing (Argon2id – NIST/NSA preferred)
    # ──────────────────────────────────────────────────────────────────────────────
    password_hashing_scheme: Literal["argon2"] = Field(
        default="argon2",
        description="Password hashing scheme (argon2 is the only supported production option)",
    )
    argon2_time_cost: int = Field(
        default=2,
        ge=1,
        le=10,
        description=(
            "Argon2 time cost (iterations). Lower on Pi (1–3), higher on PC (3–6). "
            "Target ~0.5–1 second hashing time."
        ),
    )
    argon2_memory_cost: int = Field(
        default=65536,  # 64 MiB
        ge=32768,  # 32 MiB minimum
        le=1048576,  # 1 GiB maximum (Pi-safe upper limit)
        description=(
            "Argon2 memory cost in KiB. Lower on Pi (32768–65536), higher on PC (131072+). "
            "Memory-hardness is key to resistance against GPU/ASIC attacks."
        ),
    )
    argon2_parallelism: int = Field(
        default=4,
        ge=1,
        le=8,
        description=(
            "Argon2 parallelism (threads). Keep modest on Pi (2–4), can go higher on PC (4–8)."
        ),
    )


# Singleton instance — import and use directly
auth_settings: AuthSettings = AuthSettings()

__all__ = [
    "AuthSettings",
    "auth_settings",
]
