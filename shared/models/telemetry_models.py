"""Pydantic models for raw telemetry samples, payloads, and engineered feature vectors.

This module defines validated structures for:
- Raw device telemetry readings (TelemetrySampleModel)
- Aggregated payloads sent over MQTT or to central processing (TelemetryPayloadModel)
- Processed feature vectors ready for ML/RL inference (FeatureVectorModel)

All models are self-contained, use UTC timestamps, and enforce strict validation.
No ORM or FAISS storage is required — these are transient or in-flight data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetrySampleModel(BaseModel):
    """Single raw telemetry reading from a network device or interface."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when sample was collected",
    )
    device_id: str = Field(
        ...,
        min_length=1,
        description="Unique device identifier (MAC, IP, Omada ID, etc.)",
    )
    interface: Optional[str] = Field(
        default=None,
        description="Interface name (e.g. 'eth0', 'wlan0', 'port-5')",
    )
    latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Round-trip latency in milliseconds",
    )
    packet_loss_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Packet loss percentage",
    )
    tx_bytes: int = Field(
        ...,
        ge=0,
        description="Transmitted bytes since last sample or boot",
    )
    rx_bytes: int = Field(
        ...,
        ge=0,
        description="Received bytes since last sample or boot",
    )
    cpu_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Device CPU utilization percentage",
    )
    temp_c: Optional[float] = Field(
        default=None,
        ge=-20.0,
        le=120.0,
        description="Device temperature in Celsius",
    )
    clients_connected: int = Field(
        default=0,
        ge=0,
        description="Number of connected clients (e.g. Wi-Fi associations)",
    )

    @field_validator("packet_loss_pct", mode="after")
    @classmethod
    def round_loss(cls, v: float) -> float:
        """Round packet loss to 4 decimal places for precision."""
        return round(v, 4)


class TelemetryPayloadModel(BaseModel):
    """Validated telemetry packet sent from edge to central processing or MQTT."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the aggregated payload",
    )
    latency_ms: float = Field(..., ge=0.0, description="Aggregated/average latency")
    packet_loss: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized packet loss rate (0.0–1.0)",
    )
    device_id: str = Field(..., min_length=1, description="Device identifier")
    client_count: int = Field(..., ge=0, description="Number of connected clients")

    @field_validator("packet_loss", mode="after")
    @classmethod
    def clamp_loss(cls, v: float) -> float:
        """Clamp packet loss to valid [0.0, 1.0] range."""
        return max(0.0, min(1.0, v))


class FeatureVectorModel(BaseModel):
    """Processed feature vector ready for ML/RL inference (immutable).

    Engineered from raw telemetry samples — used as input to anomaly detection,
    Q-Learning, GNNs, etc.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        frozen=True,  # Immutable after engineering
    )

    device_id: str = Field(
        ..., min_length=1, description="Originating device identifier"
    )
    timestamp: datetime = Field(
        ...,
        description="UTC timestamp of the feature window",
    )
    latency_mean_30s: float = Field(
        ...,
        ge=0.0,
        description="Average latency over the last 30 seconds",
    )
    packet_loss_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Packet loss rate over the window (0.0–1.0)",
    )
    bandwidth_trend: float = Field(
        ...,
        description="Trend direction/slope of bandwidth usage",
    )
    client_density: int = Field(
        ...,
        ge=0,
        description="Number of connected clients (density indicator)",
    )
    interference_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized interference/noise score",
    )
    extra_features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional engineered features (e.g. SNR, channel utilization)",
    )


__all__ = [
    "TelemetrySampleModel",
    "TelemetryPayloadModel",
    "FeatureVectorModel",
]
