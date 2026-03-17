"""Central configuration management for Network-Chan using Pydantic Settings.

All application-wide and component-shared settings are defined here.
Loaded automatically from .env / .env.local in current working directory.

Environment variables are prefixed (APP_ for general, MQTT_ for broker).
Sensitive values (passwords, keys) are wrapped in SecretStr for safe logging.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# Constants / Enums (human-readable mapping for docs & validation)
# =============================================================================
AUTONOMY_LEVELS = {
    0: "Observer",
    1: "Advisor",
    2: "Supervised",
    3: "Semi-Autonomous",
    4: "Autonomous",
    5: "Experimental",
}


class Settings(BaseSettings):
    """Security-sensitive and bootstrap settings (loaded early)."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),  # ← use tuple like AppSettings
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",  # safer
        env_ignore_empty=True,
    )

    # Security (required via env)
    SECRET_KEY: SecretStr = Field(
        default=...,
        validation_alias="SECRET_KEY",
        description="Required secret key for JWT / sessions / crypto",
    )
    JWT_SECRET: SecretStr = Field(
        default=...,
        validation_alias="JWT_SECRET",
        description="Secret for signing JWT tokens",
    )
    PASSWORD_SALT: SecretStr = Field(
        default=...,
        validation_alias="PASSWORD_SALT",
        description="Salt for password hashing",
    )

    # Users (MVP: single admin user; later move to SQLite)
    ADMIN_USERNAME: str = Field(default="admin")
    ADMIN_PASSWORD_HASH: str = Field(
        default=...,
        validation_alias="ADMIN_PASSWORD_HASH",
        description="bcrypt hash of admin password",
    )
    ADMIN_TOTP_SECRET: str | None = Field(
        default=None,
        validation_alias="ADMIN_TOTP_SECRET",
        description="Base32 TOTP secret (empty = 2FA disabled)",
    )

    # Quick helper
    def is_2fa_enabled(self) -> bool:
        """Check if TOTP 2FA is configured for the admin user."""
        return bool(self.ADMIN_TOTP_SECRET)


class AppSettings(BaseSettings):
    """Core application settings (autonomy mode, logging, paths, etc.)."""

    # (your existing content – unchanged, already good)
    autonomous_mode: Literal[0, 1, 2, 3, 4, 5] = Field(
        default=3,
        description="Autonomy level: 0=Observer → 5=Experimental",
    )
    # ... rest as before ...

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
        env_ignore_empty=True,
    )


class MQTTSettings(BaseSettings):
    """MQTT broker connection settings."""

    # (your existing content – already solid)
    broker: str = Field(default="localhost", description="MQTT broker hostname/IP")
    # ... rest as before ...

    model_config = SettingsConfigDict(
        env_prefix="MQTT_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="forbid",
        env_ignore_empty=True,
    )


# =============================================================================
# Public singletons – import from here
# =============================================================================
settings = Settings()  # ← renamed from Settings to avoid confusion
app_settings = AppSettings()
mqtt_settings = MQTTSettings()

__all__ = [
    "settings",
    "app_settings",
    "mqtt_settings",
    "Settings",
    "AppSettings",
    "MQTTSettings",
    "AUTONOMY_LEVELS",
]
