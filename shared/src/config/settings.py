"""Central configuration management for Network-Chan using Pydantic Settings.

All application-wide and component-shared settings are defined here.
Loaded automatically from .env / .env.local in current working directory.
"""

from typing import List, Dict, Optional, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Constants (not from env – hardcoded enum-like mapping)
AUTONOMOUS_MODES: Dict[int, str] = {
    0: "Observer",
    1: "Advisor",
    2: "Supervised",
    3: "Semi-Autonomous",
    4: "Autonomous",
    5: "Experimental",
}


class AppSettings(BaseSettings):
    """Core application settings (autonomy, logging, paths, etc.)."""

    # Autonomy & Safety
    autonomous_mode: Literal[0, 1, 2, 3, 4, 5] = Field(
        3,
        description="0=Observer, 1=Advisor, 2=Supervised, 3=Semi-Autonomous, 4=Autonomous, 5=Experimental",
    )
    whitelist_actions: List[str] = Field(
        ["reset_interface", "throttle_bandwidth"],
        description="Comma-separated list of allowed remediation actions",
    )

    # Access Control / RBAC
    role: Literal["admin", "user", "guest"] = Field(
        "admin", description="User role for access control"
    )

    # Logging & Maintenance
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field("INFO")
    prune_days: int = Field(90, ge=0, description="Days to retain logs before pruning")

    # Paths
    db_path: str = Field("network_chan.db", description="SQLite database path")
    model_path: str = Field("mock_model.onnx", description="Path to ONNX/TFLite model")

    # Audit scheduling
    audit_mode: Literal["auto", "off-peak", "always"] = Field("off-peak")

    @field_validator("autonomous_mode")
    @classmethod
    def validate_mode(cls, v: int) -> int:
        if v not in AUTONOMOUS_MODES:
            raise ValueError(f"Invalid AUTONOMOUS_MODE: {v}. Must be 0–5.")
        return v

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class MQTTSettings(BaseSettings):
    """MQTT connection configuration."""

    broker: str = Field("localhost", description="MQTT broker hostname or IP")
    port: int = Field(1883, ge=1, le=65535)
    client_id: str = Field("network-chan-client")
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    tls_ca_cert: Optional[str] = None
    tls_insecure: bool = Field(False, description="Allow insecure TLS (testing only)")
    keepalive: int = Field(60, ge=0)

    model_config = SettingsConfigDict(
        env_prefix="MQTT_",
        env_file=(".env", ".env.local"),  # Same as AppSettings
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Convenience singletons – import these directly
app_settings = AppSettings()  # type: ignore[call-arg]
mqtt_settings = MQTTSettings()  # type: ignore[call-arg]
