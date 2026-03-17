"""Pydantic models for raw telemetry samples and engineered feature vectors."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, field_validator

from .base import NetworkChanBaseModel


class TelemetrySample(NetworkChanBaseModel):
    """Single telemetry reading from a network device or interface."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    device_id: str = Field(min_length=1, description="Unique device identifier")
    interface: str | None = None
    latency_ms: float = Field(ge=0, description="Round-trip latency in ms")
    packet_loss_pct: float = Field(ge=0, le=100, description="Packet loss percentage")
    tx_bytes: int = Field(ge=0)
    rx_bytes: int = Field(ge=0)
    cpu_percent: float | None = Field(None, ge=0, le=100)
    temp_c: float | None = Field(None, ge=-20, le=120)
    clients_connected: int = Field(ge=0, default=0)

    @field_validator("packet_loss_pct", mode="after")
    @classmethod
    def round_loss(cls, v: float) -> float:
        return round(v, 4)


class FeatureVector(NetworkChanBaseModel):
    """Processed feature vector ready for ML/RL inference (immutable)."""

    model_config = ConfigDict(frozen=True)

    device_id: str
    timestamp: datetime
    latency_mean_30s: float = Field(ge=0)
    packet_loss_rate: float = Field(ge=0, le=1)
    bandwidth_trend: float
    client_density: int = Field(ge=0)
    interference_score: float = Field(ge=0, le=1)
    extra_features: dict[str, Any] = Field(default_factory=dict)
