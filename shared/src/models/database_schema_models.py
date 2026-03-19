"""Pydantic v2 models for database entities in Network-Chan.

These models are used for validation, serialization, and ORM mapping.
They follow the schema described in docs/database_schema.md.
"""

from datetime import datetime
from typing import Any, List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentBase(BaseModel):
    """Base fields common to all Incident variants."""

    incident_type: str = Field(
        ...,
        description="Type/category of the incident (e.g. 'link_flap', 'high_latency')",
    )
    device_mac: Optional[str] = Field(
        None, description="MAC address of the primary affected device"
    )
    device_ip: Optional[str] = Field(
        None, description="IP address of the primary device"
    )
    description: str = Field(..., description="Human-readable summary")
    severity: Literal["info", "warning", "error", "critical"] = Field(default="warning")
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Flexible key-value context"
    )


class IncidentCreate(IncidentBase):
    """Fields required when creating a new incident."""

    timestamp_start: datetime = Field(..., description="When the incident began")
    affected_devices: List[str] = Field(
        default_factory=list, description="List of affected device identifiers"
    )


class IncidentRead(IncidentBase):
    """Fields returned when reading an incident (includes database-generated fields)."""

    id: UUID = Field(..., description="Unique incident identifier")
    timestamp_start: datetime
    timestamp_end: Optional[datetime] = Field(
        None, description="When the incident was resolved (null if active)"
    )
    resolved: bool = Field(default=False)
    resolution_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelRegistryBase(BaseModel):
    """Base fields for ML model registry entries."""

    model_name: str = Field(..., description="Name/identifier of the model")
    version: str = Field(..., description="Semantic version or commit hash")
    model_type: Literal["tinyml", "q_learning", "gnn", "rl_maml", "other"]
    description: Optional[str] = None
    trained_on: Optional[datetime] = None
    performance_metrics: dict[str, float] = Field(default_factory=dict)


class ModelCreate(ModelRegistryBase):
    """Fields required when registering a new model version."""

    model_hash: str = Field(
        ..., description="Content hash (sha256) of serialized model"
    )
    file_path: Optional[str] = Field(
        None, description="Path to model file if stored locally"
    )


class ModelRead(ModelRegistryBase):
    """Read representation of a model registry entry."""

    id: UUID
    model_hash: str
    file_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyAuditBase(BaseModel):
    """Base fields for policy enforcement audit logs."""

    incident_id: Optional[UUID] = Field(
        None, description="Incident this action relates to (if any)"
    )
    action_taken: str = Field(
        ..., description="Description of the action (e.g. 'port disable')"
    )
    executed_by: Literal["human", "autonomous", "policy_engine"]
    approved_by: Optional[str] = None
    success: bool = Field(default=True)
    error_message: Optional[str] = None


class PolicyAuditCreate(PolicyAuditBase):
    """Fields when logging a new policy action."""

    timestamp: datetime = Field(..., description="When the action occurred")


class PolicyAuditRead(PolicyAuditBase):
    """Read representation of a policy audit entry."""

    id: UUID
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
