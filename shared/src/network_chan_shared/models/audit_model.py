"""Pydantic schemas, SQLAlchemy ORM record, and FAISS embedding model for audit events.

This module defines the immutable audit trail records for every significant system event:
policy decisions, action executions, config changes, mode switches, etc.
All records are UTC-timestamped and frozen for integrity.
"""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from sqlalchemy import Boolean, DateTime, String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from ..models.sqlite_models import Base


class AuditEventModel(BaseModel):
    """Immutable audit event record — used for logging, transfer, and validation.

    Frozen to prevent any mutation after creation (audit integrity).
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        frozen=True,
    )

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique UUID for this audit entry (string form)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the event occurred",
    )
    actor: str = Field(
        ...,
        min_length=1,
        description="Who/what triggered the event: user ID, 'system', 'appliance-pi-01', etc.",
    )
    action_type: str = Field(
        ...,
        min_length=1,
        description="Type of action: 'policy_check', 'action_executed', 'mode_changed', 'login', etc.",
    )
    target: Optional[str] = Field(
        default=None,
        description="Resource affected: device MAC, user ID, policy ID, etc.",
    )
    before_state: Optional[dict[str, Any]] = Field(
        default=None,
        description="Snapshot of relevant state before the change (JSON-serializable)",
    )
    after_state: Optional[dict[str, Any]] = Field(
        default=None,
        description="Snapshot of relevant state after the change",
    )
    approved: bool = Field(
        default=True,
        description="Whether the action was explicitly approved (false = autonomous override)",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Human or system justification (required for manual overrides)",
    )
    related_incident_id: Optional[str] = Field(
        default=None,
        description="UUID of related incident (links audit to incident log)",
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="Source IP address if event was user-initiated",
    )


class AuditEventRecord(Base):
    """Persistent SQLite storage for audit events.

    Append-only table for compliance, traceability, and FAISS semantic search.
    Inherits automatic created_at / updated_at from Base.
    """

    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Unique UUID for this audit record",
    )
    event_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True,
        doc="String UUID from AuditEventModel (for consistency with external logs)",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="UTC timestamp of the event",
    )
    actor: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Actor identifier (user, system component, etc.)",
    )
    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of audited action",
    )
    target: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Affected resource identifier",
    )
    before_state: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Pre-change state snapshot",
    )
    after_state: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        doc="Post-change state snapshot",
    )
    approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Was the action explicitly approved?",
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Justification or system reasoning",
    )
    related_incident_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        doc="Link to related incident UUID",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="Source IP if user-initiated",
    )

    __table_args__ = (
        Index("ix_audit_events_timestamp", "timestamp"),
        Index("ix_audit_events_actor", "actor"),
        Index("ix_audit_events_action_type", "action_type"),
        Index("ix_audit_events_related_incident_id", "related_incident_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEventRecord id={self.id} event_id={self.event_id} "
            f"actor={self.actor} action={self.action_type}>"
        )


class AuditEventEmbedding(BaseModel):
    """FAISS-ready embedding representation for audit events.

    Lightweight wrapper for vector + key metadata used during indexing and retrieval.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    vector: list[float] = Field(
        ...,
        description="High-dimensional embedding vector (e.g. 384-dim from MiniLM)",
    )
    action_type: str
    actor: str
    timestamp: datetime
    approved: bool
    description: Optional[str] = Field(default=None, max_length=500)


__all__ = [
    "AuditEventModel",
    "AuditEventRecord",
    "AuditEventEmbedding",
]
