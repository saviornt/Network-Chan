"""Pydantic models for tracking network incidents from detection to resolution."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from .anomaly import AnomalyDetectionResult
from .base import NetworkChanBaseModel
from .rl import RLAction


class IncidentLogEntry(NetworkChanBaseModel):
    """Immutable record of a detected incident and its lifecycle."""

    model_config = {"frozen": True}

    incident_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID for this incident",
    )
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    affected_devices: list[str] = Field(
        default_factory=list, description="Device IDs involved"
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(...)
    description: str = Field(min_length=10)
    root_cause: str | None = None
    trigger: AnomalyDetectionResult | None = Field(
        default=None, description="Original anomaly that started the incident"
    )
    remediation_action: RLAction | None = Field(
        default=None, description="Action that was (or will be) executed"
    )
    outcome: Literal["resolved", "mitigated", "failed", "ongoing"] = Field(
        default="ongoing"
    )
    resolution_notes: str | None = None
    duration_seconds: float | None = Field(
        default=None, ge=0, description="Calculated when end_time is set"
    )

    @model_validator(mode="after")
    def validate_chronology(self) -> IncidentLogEntry:
        """Ensure chronological consistency between start_time and end_time."""
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
        return self

    @model_validator(mode="after")
    def calculate_duration(self) -> IncidentLogEntry:
        """Auto-calculate duration_seconds when both timestamps are present."""
        if self.end_time and self.start_time:
            delta = (self.end_time - self.start_time).total_seconds()
            object.__setattr__(self, "duration_seconds", max(0.0, delta))
        return self
