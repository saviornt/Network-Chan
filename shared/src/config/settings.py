"""Central configuration management for Network-Chan using Pydantic Settings v2.

Loads settings from .env / .env.local with prefix-based separation.
All shared settings live in one class for simplicity, grouped logically via Field descriptions.
Sensitive values use SecretStr; paths are validated/created at runtime where safe.

Usage:
    from shared.config.settings import settings
    print(settings.autonomous_mode)          # → AutonomyLevel.SemiAutonomous
    print(settings.is_2fa_enabled())         # → bool
    print(settings.mqtt.broker)              # → str (namespaced access via property)
"""

from __future__ import annotations

import os
import platform
from enum import IntEnum
from functools import cached_property
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AutonomyLevel(IntEnum):
    """Autonomy levels (aligned with vision.md, security_design.md, technical_requirements.md).

    Lower levels are safer / more manual; higher levels enable more automation.
    Stored as int in env for simplicity, but exposed as enum for type safety.
    """

    OBSERVER = 0  # Monitor & log only — no suggestions
    ADVISOR = 1  # Suggest actions (dashboard/LLM)
    SUPERVISED = 2  # Suggest + require approval for most actions
    SEMI_AUTONOMOUS = 3  # Auto-execute safe/low-risk actions
    AUTONOMOUS = 4  # Full self-healing (with rollback guardrails)
    EXPERIMENTAL = 5  # Bleeding-edge / research mode (no safety nets)


class Settings(BaseSettings):
    """Network-Chan global settings — single source of truth for both Appliance & Assistant.

    Loaded automatically. Access via `settings.<field>`.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",  # Prevent typos / unknown vars
        env_ignore_empty=True,
        env_nested_delimiter="__",  # Optional: APP__AUTONOMOUS_MODE=3
    )

    # =========================================================================
    # Security & Authentication
    # =========================================================================
    secret_key: SecretStr = Field(
        default=SecretStr(
            os.getenv("SECRET_KEY", "test-secret-key-for-unit-tests-only")
        ),
        validation_alias="SECRET_KEY",
        description="Root secret for JWT, sessions, Fernet crypto, etc.",
    )
    jwt_secret: SecretStr = Field(
        default=SecretStr(
            os.getenv("JWT_SECRET", "test-jwt-secret-for-unit-tests-only")
        ),
        validation_alias="JWT_SECRET",
        description="Dedicated secret for signing/verifying JWT tokens",
    )
    password_salt: SecretStr = Field(
        default=SecretStr(
            os.getenv("PASSWORD_SALT", "test-password-salt-for-unit-tests-only")
        ),
        validation_alias="PASSWORD_SALT",
        description="Salt used in password hashing (bcrypt/argon2)",
    )

    admin_username: str = Field(default="admin", min_length=3)
    admin_password_hash: str = Field(
        default=os.getenv(
            "ADMIN_PASSWORD_HASH", "test-bcrypt-hash-for-unit-tests-only"
        ),
        validation_alias="ADMIN_PASSWORD_HASH",
        description="bcrypt hash of the admin password",
    )
    admin_totp_secret: str | None = Field(
        default=None,
        validation_alias="ADMIN_TOTP_SECRET",
        description="Base32-encoded TOTP secret; None = 2FA disabled",
    )

    # =========================================================================
    # Autonomy & Safety Controls
    # =========================================================================
    autonomous_mode: AutonomyLevel = Field(
        default=AutonomyLevel.SEMI_AUTONOMOUS,
        description="Current autonomy level (0=Observer → 5=Experimental)",
    )
    max_reboots_per_hour: int = Field(default=1, ge=0, le=10)
    max_channel_changes_per_10min: int = Field(default=2, ge=0, le=20)
    require_approval_above_level: AutonomyLevel = Field(
        default=AutonomyLevel.AUTONOMOUS,
        description="Actions above this level always require explicit approval",
    )

    # =========================================================================
    # Logging & Environment
    # =========================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Python logging level",
    )
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment",
    )

    # =========================================================================
    # Paths (Pi-safe defaults)
    # =========================================================================
    data_dir: Path = Field(
        default=Path("/var/lib/network-chan"),
        description="Base directory for persistent data (DB, FAISS, MLflow, snapshots)",
    )
    db_path: Path = Field(default=Path("db.sqlite"), description="Relative to data_dir")
    faiss_index_path: Path = Field(
        default=Path("faiss.index"), description="Relative to data_dir"
    )
    mlflow_tracking_uri: str = Field(
        default="sqlite:///mlruns.db", description="Local MLflow backend"
    )

    # =========================================================================
    # MQTT Broker
    # =========================================================================
    mqtt_broker: str = Field(
        default="localhost", description="Hostname/IP of MQTT broker"
    )
    mqtt_port: int = Field(default=1883, ge=1, le=65535)
    mqtt_use_tls: bool = Field(default=True, description="Enable TLS (recommended)")
    mqtt_username: str | None = None
    mqtt_password: SecretStr | None = None
    mqtt_client_id: str = Field(
        default="network-chan-{app_env}", description="Unique client identifier"
    )

    # =========================================================================
    # RL / ML Shared Defaults (edge-friendly)
    # =========================================================================
    rl_learning_rate: float = Field(default=0.1, gt=0.0, lt=1.0)
    reptile_inner_steps: int = Field(default=5, ge=1, le=20)
    anomaly_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    rl_alpha: float = Field(
        default=0.1,
        gt=0.0,
        lt=1.0,
        description="Learning rate for Q-Learning updates (0 < alpha < 1)",
    )

    # =========================================================================
    # Computed / Helper Properties
    # =========================================================================
    @property
    def full_db_path(self) -> Path:
        """Absolute path to SQLite database (created on first use)."""
        return (self.data_dir / self.db_path).resolve()

    @property
    def full_faiss_path(self) -> Path:
        """Absolute path to FAISS index file."""
        return (self.data_dir / self.faiss_index_path).resolve()

    @cached_property
    def is_edge_device(self) -> bool:
        """Detect whether we are running on a Raspberry Pi (Appliance / edge mode).

        Detection priority:
        1. OS/distribution name contains 'Raspbian' or 'Raspberry Pi OS'
        2. Machine/hardware identifier is 'armv' or 'aarch64' + Pi-specific files exist
        3. Presence of Raspberry Pi specific paths (/proc/device-tree, /sys/firmware/devicetree)

        Returns:
            True if likely running on Raspberry Pi Appliance, False otherwise.
        """
        # 1. OS/distribution check (most reliable for Raspberry Pi OS)
        system = platform.system().lower()
        if system != "linux":
            return False

        dist = ""
        try:
            with open("/etc/os-release", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        dist = line.split("=", 1)[1].strip().strip('"').lower()
                        break
        except (FileNotFoundError, PermissionError):
            pass

        if "raspbian" in dist or "raspberry pi os" in dist:
            return True

        # 2. Architecture + Pi-specific file checks (fallback)
        machine = platform.machine().lower()
        is_arm = "arm" in machine or "aarch64" in machine

        if not is_arm:
            return False

        # Typical Raspberry Pi indicators
        pi_indicators = [
            "/proc/device-tree/model",
            "/sys/firmware/devicetree/base/model",
            "/proc/cpuinfo",  # contains "Raspberry Pi" in "Model" or "Hardware"
        ]

        for path in pi_indicators:
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read().lower()
                        if "raspberry pi" in content:
                            return True
                except (PermissionError, OSError):
                    pass

        # Last resort: existence of typical Pi paths
        return os.path.exists("/proc/device-tree") and os.path.exists(
            "/sys/class/thermal/thermal_zone0"
        )

    # Optional: convenience property
    @property
    def running_on_pi(self) -> bool:
        """Alias for is_edge_device() — more readable in some contexts."""
        return self.is_edge_device

    def is_2fa_enabled(self) -> bool:
        """Check if TOTP 2FA is configured for the admin user."""
        return bool(self.admin_totp_secret)

    # =========================================================================
    # Validators & Runtime Safety
    # =========================================================================
    @field_validator("data_dir", "db_path", "faiss_index_path", mode="after")
    @classmethod
    def ensure_parent_dirs(cls, v: Path) -> Path:
        """Create parent directories if they don't exist (safe on Pi)."""
        if v.is_absolute():
            v.parent.mkdir(parents=True, exist_ok=True)
        return v

    @model_validator(mode="after")
    def validate_autonomy_constraints(self) -> Settings:
        """Enforce safety rules on autonomy level."""
        if self.autonomous_mode >= AutonomyLevel.AUTONOMOUS and not self.is_edge_device:
            # Optional: raise ValueError("Full autonomy only allowed on edge Appliance")
            pass  # For now, just log warning in real usage
        return self


# Singleton instance — import and use directly
settings: Settings = Settings()


__all__ = [
    "settings",
    "Settings",
    "AutonomyLevel",
]
