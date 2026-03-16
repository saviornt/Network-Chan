# shared/src/models.py
"""Pydantic v2 models for all data validation across repo.

Strict types, JSON schema export for FastAPI, field validators.
"""

from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, Field, field_validator


class TelemetryPayload(BaseModel):
    """Validated telemetry packet (used by edge & assistant)."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float = Field(ge=0)
    packet_loss: float = Field(ge=0, le=1)
    device_id: str
    client_count: int = Field(ge=0)

    @field_validator("packet_loss")
    @classmethod
    def clamp_loss(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class RLAction(BaseModel):
    action_type: Literal["channel_change", "client_reassign", "reboot"]
    params: Dict[str, str | int]
    confidence: float = Field(ge=0, le=1, default=0.95)
