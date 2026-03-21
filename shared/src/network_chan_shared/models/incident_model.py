"""Pydantic schemas, SQLAlchemy ORM record, and FAISS embedding model for network incidents.

This file handles:
- Incident creation/validation (Pydantic)
- Persistent storage (ORM)
- Lifecycle logging (IncidentLogEntry)
- Semantic search via FAISS
"""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sqlalchemy import Boolean, DateTime, Index, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..models.sqlite_models import Base
from ..models.anomaly_model import AnomalyDetectionResultModel
from ..models.rl_core_models import RLAction


class IncidentBaseModel(BaseModel):
    """Shared base fields for all Incident Pydantic schemas."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    incident_type: str = Field(
        ...,
        description="Type/category of the incident (e.g. 'link_flap', 'high_latency')",
    )
    device_mac: Optional[str] = Field(
        None,
        description="MAC address of the primary affected device",
    )
    device_ip: Optional[str] = Field(
        None,
        description="IP address of the primary device",
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Human-readable summary of the incident",
    )
    severity: Literal["info", "warning", "error", "critical"] = Field(
        default="warning",
        description="Severity level",
    )
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible key-value context",
    )


class IncidentCreateModel(IncidentBaseModel):
    """Fields required when creating a new incident."""

    timestamp_start: datetime = Field(
        ...,
        description="When the incident began",
    )
    affected_devices: List[str] = Field(
        default_factory=list,
        description="List of affected device identifiers (MACs, IPs, etc.)",
    )


class IncidentModel(IncidentBaseModel):
    """Full read representation of an incident (includes DB-generated fields)."""

    id: UUID = Field(..., description="Unique incident identifier")
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = Field(
        None,
        description="When the incident was resolved (null if active)",
    )
    resolved: bool = Field(default=False)
    resolution_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncidentLogEntry(BaseModel):
    """Immutable record of an incident lifecycle — from detection to resolution.

    Separate from the core Incident record; used for detailed event history.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    incident_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique UUID for this incident (string form)",
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the incident was first detected",
    )
    end_time: Optional[datetime] = Field(default=None)
    affected_devices: list[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high", "critical"] = Field(...)
    description: str = Field(min_length=10)
    root_cause: Optional[str] = None
    trigger: Optional[AnomalyDetectionResultModel] = Field(default=None)
    remediation_action: Optional[RLAction] = Field(default=None)
    outcome: Literal["resolved", "mitigated", "failed", "ongoing"] = Field(
        default="ongoing"
    )
    resolution_notes: Optional[str] = None
    duration_seconds: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_chronology(self) -> "IncidentLogEntry":
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValueError("end_time cannot be before start_time")
        return self

    @model_validator(mode="after")
    def calculate_duration(self) -> "IncidentLogEntry":
        if self.end_time and self.start_time:
            delta = (self.end_time - self.start_time).total_seconds()
            object.__setattr__(self, "duration_seconds", max(0.0, delta))
        return self


class IncidentRecord(Base):
    """Persistent SQLite storage for network incidents and anomalies."""

    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    device_mac: Mapped[Optional[str]] = mapped_column(
        String(17), nullable=True, index=True
    )
    device_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="warning"
    )
    extra_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    timestamp_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    timestamp_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    affected_devices: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    __table_args__ = (
        Index("ix_incidents_timestamp_start", "timestamp_start"),
        Index("ix_incidents_device_mac", "device_mac"),
        Index("ix_incidents_incident_type", "incident_type"),
        Index("ix_incidents_resolved", "resolved"),
    )

    def __repr__(self) -> str:
        return f"<IncidentRecord id={self.id} type={self.incident_type} severity={self.severity} resolved={self.resolved}>"


class IncidentEmbedding(BaseModel):
    """FAISS-ready embedding for incidents (for semantic RAG search)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    vector: list[float] = Field(...)
    incident_type: str
    severity: str
    timestamp_start: datetime
    description: Optional[str] = Field(default=None, max_length=500)


__all__ = [
    "IncidentBaseModel",
    "IncidentCreateModel",
    "IncidentModel",
    "IncidentLogEntry",
    "IncidentRecord",
    "IncidentEmbedding",
]
