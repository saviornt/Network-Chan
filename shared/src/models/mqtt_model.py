"""Pydantic models for MQTT message payloads and metadata.

These models define standardized shapes for publishing and subscribing across
the Network-Chan system (edge → broker → assistant, control messages, etc.).
All payloads are validated before publish or after receive.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, Json, field_validator, SecretStr

from .base_model import NetworkChanBaseModel
from .policy_model import PolicyDecision
from .rl_model import RLAction
from .telemetry_model import TelemetrySample
from shared.src.config.mqtt_settings import mqtt_settings
from shared.src.config.shared_settings import shared_settings


class MqttMessageMetadata(NetworkChanBaseModel):
    """Common metadata wrapper for every MQTT message (used in both pub/sub)."""

    topic: str = Field(
        min_length=1,
        description="Full MQTT topic (e.g. 'network-chan/telemetry/ap-01')",
    )
    qos: Literal[0, 1, 2] = Field(default=1, description="MQTT QoS level")
    retain: bool = Field(default=False, description="Whether to retain message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: str | None = Field(
        default=None,
        description="Optional unique message UUID (for correlation/tracking)",
    )
    sender: str = Field(
        ..., description="Sender identifier (e.g. 'appliance-pi-01', 'assistant')"
    )


class MqttTelemetryPublish(NetworkChanBaseModel):
    """Payload shape for publishing telemetry samples from edge to broker."""

    metadata: MqttMessageMetadata
    payload: TelemetrySample | list[TelemetrySample] = Field(
        description="Single sample or batch of recent samples"
    )

    @field_validator("payload", mode="before")
    @classmethod
    def normalize_payload(
        cls,
        v: Dict[str, Any] | List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Normalize payload to always be a list of dicts."""
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list):
            if not all(isinstance(item, dict) for item in v):
                raise ValueError("All items in payload list must be dicts")
            return v
        raise ValueError("payload must be a dict or list of dicts")


class MqttControlCommand(NetworkChanBaseModel):
    """Standardized shape for control/policy messages sent to the edge appliance."""

    metadata: MqttMessageMetadata
    command_type: Literal[
        "set_autonomy_mode",
        "force_retrain",
        "execute_action",
        "rollback_last",
        "update_policy",
        "shutdown",
    ]
    parameters: dict[str, Any] = Field(default_factory=dict)
    requested_by: str | None = None
    correlation_id: str | None = Field(
        default=None, description="For request-response pairing"
    )


class MqttActionExecution(NetworkChanBaseModel):
    """Payload published after an action is executed (success/failure)."""

    metadata: MqttMessageMetadata
    action: RLAction
    success: bool
    result_message: str = Field(default="")
    exit_code: int | None = None
    duration_seconds: float | None = Field(default=None, ge=0)
    error_details: str | None = None


class MqttPolicyDecisionPublish(NetworkChanBaseModel):
    """When the central assistant publishes a policy decision back to edge."""

    metadata: MqttMessageMetadata
    decision: PolicyDecision
    original_request_id: str | None = Field(
        default=None, description="Links back to the original PolicyCheckRequest"
    )


class MqttRawPayload(NetworkChanBaseModel):
    """Fallback / generic wrapper for unknown or future message types."""

    metadata: MqttMessageMetadata
    raw_payload: Json[Any] = Field(
        ..., description="Arbitrary JSON-serializable content"
    )


class MqttClientOptions(NetworkChanBaseModel):
    """
    Validated runtime options for creating an MQTT client.

    Aggregates settings from mqtt_settings + optional overrides.
    Used as input to create_secure_mqtt_client().
    """

    hostname: str = Field(..., description="MQTT broker hostname or IP")
    port: int = Field(..., ge=1, le=65535, description="Broker port")
    client_id: str = Field(..., min_length=1, description="Unique client identifier")
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)  # Plain str (SecretStr unwrapped)
    tls_enabled: bool = Field(default=True)
    ca_cert_path: Optional[Path] = Field(default=None)
    client_cert_path: Optional[Path] = Field(default=None)
    client_key_path: Optional[Path] = Field(default=None)
    keepalive: int = Field(default=60, ge=1)
    connect_timeout: float = Field(default=10.0, ge=1.0)

    @field_validator("password", mode="before")
    @classmethod
    def unwrap_password(cls, v: Any) -> Optional[str]:
        """Convert SecretStr to plain string if present."""
        if isinstance(v, SecretStr):
            return v.get_secret_value()
        return v

    @classmethod
    def from_settings(
        cls, overrides: dict[str, Any] | None = None
    ) -> "MqttClientOptions":
        """
        Build options from mqtt_settings + optional runtime overrides.

        Automatically formats client_id with app_env if template present.
        """
        data = mqtt_settings.model_dump(exclude_none=True)
        if overrides:
            data.update(overrides)

        # Unwrap password if SecretStr
        if mqtt_settings.password:
            data["password"] = mqtt_settings.password.get_secret_value()

        # Format client_id if it contains {app_env}
        if "{app_env}" in data.get("client_id", ""):
            data["client_id"] = data["client_id"].format(
                app_env=shared_settings.app_env
            )

        return cls.model_validate(data)
