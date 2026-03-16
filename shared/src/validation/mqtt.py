"""Pydantic models for MQTT message payloads and metadata.

These models define standardized shapes for publishing and subscribing across
the Network-Chan system (edge → broker → assistant, control messages, etc.).
All payloads are validated before publish or after receive.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, Json, field_validator

from .base import NetworkChanBaseModel
from .policy import PolicyDecision
from .rl import RLAction
from .telemetry import TelemetrySample


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
    def normalize_payload(cls, v: Any) -> Any:
        """Allow single dict or list of dicts → always normalize to list."""
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list):
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
