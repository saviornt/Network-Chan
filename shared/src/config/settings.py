"""Central configuration management for Network-Chan using Pydantic Settings.

All application-wide and component-shared settings are defined here.
Loaded automatically from .env / .env.local in current working directory.

Environment variables are prefixed (APP_ for general, MQTT_ for broker).
Sensitive values (passwords, keys) are wrapped in SecretStr for safe logging.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
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
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Security
    SECRET_KEY: SecretStr = Field(..., env="SECRET_KEY")
    JWT_SECRET: SecretStr = Field(..., env="JWT_SECRET")
    PASSWORD_SALT: SecretStr = Field(..., env="PASSWORD_SALT")

    # Users (MVP: single admin user; later move to SQLite)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = Field(..., env="ADMIN_PASSWORD_HASH")  # bcrypt hash
    ADMIN_TOTP_SECRET: str | None = None  # base32 TOTP secret (empty = 2FA disabled)

    # Appliance/Assistant specific
    AUTONOMY_MODE: Literal["ADVISE", "MONITOR", "AUTONOMOUS"] = "ADVISE"
    # ... other settings

    def is_2fa_enabled(self) -> bool:
        """Check if TOTP 2FA is configured for the admin user."""
        return bool(self.ADMIN_TOTP_SECRET)


class AppSettings(BaseSettings):
    """Core application settings (autonomy mode, logging, paths, etc.)."""

    # Autonomy & Safety
    autonomous_mode: Literal[0, 1, 2, 3, 4, 5] = Field(
        default=3,
        description="Autonomy level: 0=Observer → 5=Experimental",
    )
    whitelist_actions: list[str] = Field(
        default_factory=lambda: ["reset_interface", "throttle_bandwidth"],
        description="Allowed remediation actions (used by policy engine)",
    )

    # Access Control / RBAC (placeholder – extend later)
    role: Literal["admin", "operator", "viewer"] = Field(
        default="admin",
        description="Current user role for access decisions",
    )

    # Logging & Maintenance
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    prune_days: int = Field(default=90, ge=0, description="Log retention period (days)")

    # Paths
    db_path: str = Field(default="network_chan.db", description="SQLite database path")
    model_path: str = Field(
        default="models/latest.onnx", description="Default ML model path"
    )

    # Audit scheduling
    audit_mode: Literal["auto", "off-peak", "always", "manual"] = Field(
        default="off-peak"
    )

    @field_validator("autonomous_mode")
    @classmethod
    def check_valid_mode(cls, v: int) -> int:
        if v not in AUTONOMY_LEVELS:
            raise ValueError(f"Invalid autonomy level {v}. Must be 0–5.")
        return v

    @field_validator("whitelist_actions", mode="before")
    @classmethod
    def normalize_actions(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [a.strip() for a in v.split(",") if a.strip()]
        return v

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="forbid",  # safer – fail on unknown env vars
        case_sensitive=False,
        env_ignore_empty=True,  # treat empty MQTT_PASSWORD="" as None
    )


class MQTTSettings(BaseSettings):
    """MQTT broker connection settings."""

    broker: str = Field(default="localhost", description="MQTT broker hostname/IP")
    port: int = Field(default=1883, ge=1, le=65535)
    client_id: str = Field(
        default="network-chan-client", description="Unique client identifier"
    )
    username: str | None = Field(default=None)
    password: SecretStr | None = Field(default=None)  # ← this is correct & recommended
    tls_ca_cert: str | None = Field(default=None, description="Path to CA certificate")
    tls_insecure: bool = Field(
        default=False, description="Skip TLS verification (dev only)"
    )
    keepalive: int = Field(
        default=60, ge=10, description="Keep-alive interval (seconds)"
    )
    clean_session: bool = Field(default=True, description="Start with clean session")

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
app_settings = AppSettings()
mqtt_settings = MQTTSettings()


__all__ = [
    "app_settings",
    "mqtt_settings",
    "AppSettings",
    "MQTTSettings",
    "AUTONOMY_LEVELS",
]
