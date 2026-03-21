"""Pydantic models for MQTT message payloads and metadata.

These models define standardized shapes for publishing and subscribing across
the Network-Chan system (edge → broker → assistant, control messages, etc.).
All payloads are validated before publish or after receive.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, Json, SecretStr, field_validator

from ..models.policy_model import PolicyDecisionModel
from ..models.rl_core_models import RLAction
from ..models.telemetry_models import TelemetrySampleModel
from ..settings.mqtt_settings import mqtt_settings


class MqttMessageMetadata(BaseModel):
    """Common metadata wrapper for every MQTT message (pub/sub)."""

    model_config = ConfigDict(
        extra="forbid",  # reject unknown fields
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        frozen=True,  # immutable metadata
    )

    topic: str = Field(min_length=1, description="Full MQTT topic")
    qos: Literal[0, 1, 2] = Field(default=1, description="MQTT QoS level")
    retain: bool = Field(default=False, description="Retain flag")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: Optional[str] = Field(default=None, description="Correlation ID")
    sender: str = Field(..., description="Sender identifier (e.g. 'appliance-pi-01')")


class MqttTelemetryPublish(BaseModel):
    """Payload for publishing telemetry from edge to broker."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: MqttMessageMetadata
    payload: TelemetrySampleModel | list[TelemetrySampleModel] = Field(...)

    @field_validator("payload", mode="before")
    @classmethod
    def normalize_payload(cls, v: Any) -> list[dict]:
        """Normalize to list of dicts for consistency."""
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list):
            if not all(isinstance(item, dict) for item in v):
                raise ValueError("All items in payload list must be dicts")
            return v
        raise ValueError("payload must be dict or list of dicts")


class MqttControlCommand(BaseModel):
    """Control/policy command sent to the edge appliance."""

    model_config = ConfigDict(extra="forbid")

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
    requested_by: Optional[str] = None
    correlation_id: Optional[str] = Field(default=None)


class MqttActionExecution(BaseModel):
    """Published after executing an action (success/failure)."""

    model_config = ConfigDict(extra="forbid")

    metadata: MqttMessageMetadata
    action: RLAction
    success: bool
    result_message: str = Field(default="")
    exit_code: Optional[int] = None
    duration_seconds: Optional[float] = Field(default=None, ge=0)
    error_details: Optional[str] = None


class MqttPolicyDecisionPublish(BaseModel):
    """Policy decision published from assistant to edge."""

    model_config = ConfigDict(extra="forbid")

    metadata: MqttMessageMetadata
    decision: PolicyDecisionModel
    original_request_id: Optional[str] = Field(default=None)


class MqttRawPayload(BaseModel):
    """Generic fallback for unknown/future message types."""

    model_config = ConfigDict(extra="forbid")

    metadata: MqttMessageMetadata
    raw_payload: Json[Any] = Field(...)


class MqttClientOptions(BaseModel):
    """Validated runtime options for creating an MQTT client."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    hostname: str = Field(...)
    port: int = Field(..., ge=1, le=65535)
    client_id: str = Field(min_length=1)
    username: Optional[str] = None
    password: Optional[str] = None
    tls_enabled: bool = Field(default=True)
    ca_cert_path: Optional[Path] = None
    client_cert_path: Optional[Path] = None
    client_key_path: Optional[Path] = None
    keepalive: int = Field(default=60, ge=1)
    connect_timeout: float = Field(default=10.0, ge=1.0)

    @field_validator("password", mode="before")
    @classmethod
    def unwrap_password(cls, v: Any) -> Optional[str]:
        if isinstance(v, SecretStr):
            return v.get_secret_value()
        return v

    @classmethod
    def from_settings(
        cls, overrides: dict[str, Any] | None = None
    ) -> "MqttClientOptions":
        data = mqtt_settings.model_dump(exclude_none=True)
        if overrides:
            data.update(overrides)

        if mqtt_settings.password:
            data["password"] = mqtt_settings.password.get_secret_value()

        return cls.model_validate(data)


__all__ = [
    "MqttMessageMetadata",
    "MqttTelemetryPublish",
    "MqttControlCommand",
    "MqttActionExecution",
    "MqttPolicyDecisionPublish",
    "MqttRawPayload",
    "MqttClientOptions",
]
