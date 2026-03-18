"""Immutable audit trail models for all significant system events."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from .base_model import NetworkChanBaseModel


class AuditEvent(NetworkChanBaseModel):
    """Immutable record of every policy decision, action execution, or config change."""

    model_config = {"frozen": True}

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID for audit trail",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = Field(
        ..., description="User ID, system component, or 'system' for autonomous"
    )
    action_type: str = Field(
        ..., description="e.g. 'policy_check', 'action_executed', 'mode_changed'"
    )
    target: str | None = Field(
        default=None, description="Device ID, user ID, or resource affected"
    )
    before_state: dict[str, Any] | None = Field(
        default=None, description="Snapshot before change (JSON serializable)"
    )
    after_state: dict[str, Any] | None = Field(
        default=None, description="Snapshot after change"
    )
    approved: bool = Field(default=True)
    reason: str | None = None
    related_incident_id: str | None = Field(
        default=None, description="Link to incident if applicable"
    )
    ip_address: str | None = Field(
        default=None, description="Source IP if user-initiated"
    )
