"""Dedicated Pydantic Settings for MQTT broker connectivity in Network-Chan.

Handles broker address, port, TLS configuration, credentials, client ID, and connection timeouts.
Environment variables are prefixed with MQTT__ (double underscore).

Example:
    export MQTT__BROKER=192.168.1.100
    export MQTT__USE_TLS=true
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict


class MqttSettings(BaseSettings):
    """
    Configuration for connecting to the MQTT broker (Mosquitto or similar).

    All fields use the MQTT__ env prefix.
    Supports secure TLS connections with certificate validation.
    """

    model_config = SettingsConfigDict(
        env_prefix="MQTT__",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    broker: str = Field(
        default="localhost",
        description="Hostname or IP address of the MQTT broker.",
    )
    port: int = Field(
        default=8883,  # Standard secure MQTT port
        ge=1,
        le=65535,
        description="TCP port for the MQTT broker (1883 insecure, 8883 secure).",
    )
    use_tls: bool = Field(
        default=True,
        description="Enable TLS/SSL for secure communication (recommended).",
    )
    ca_cert_path: Optional[Path] = Field(
        default=None,
        description=(
            "Path to CA certificate file for broker verification. "
            "If None and use_tls=True, uses system CA store."
        ),
    )
    client_cert_path: Optional[Path] = Field(
        default=None,
        description="Path to client certificate file (mutual TLS).",
    )
    client_key_path: Optional[Path] = Field(
        default=None,
        description="Path to client private key file (mutual TLS).",
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for broker authentication (if required).",
    )
    password: Optional[SecretStr] = Field(
        default=None,
        description="Password for broker authentication (if required).",
    )
    client_id: str = Field(
        default="network-chan-{app_env}",
        description="Unique client identifier for this instance.",
    )
    connect_timeout_sec: float = Field(
        default=10.0,
        ge=1.0,
        description="Timeout for initial connection attempt (seconds).",
    )
    keepalive_sec: int = Field(
        default=60,
        ge=1,
        description="MQTT keep-alive interval (seconds).",
    )


# Singleton instance — import and use directly
mqtt_settings: MqttSettings = MqttSettings()
