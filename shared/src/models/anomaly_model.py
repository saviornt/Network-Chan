"""Models related to anomaly detection results."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base_model import NetworkChanBaseModel


class AnomalyDetectionResult(NetworkChanBaseModel):
    """Output from lightweight anomaly detection (TinyML / threshold-based)."""

    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_anomaly: bool
    anomaly_score: float = Field(ge=0, le=1)
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Human-readable severity level"
    )
    reason: str = Field(min_length=1)
    related_metrics: list[str] = Field(default_factory=list)
