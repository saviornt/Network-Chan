"""Pydantic models and SQLAlchemy ORM records for policy checks, decisions, and audits.

This module defines:
- Runtime request/response for policy evaluation
- Persistent audit logs for policy enforcement actions
"""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models.sqlite_models import Base
from ..models.rl_core_models import RLAction, RLState
from ..models.incident_model import IncidentRecord


class PolicyCheckRequestModel(BaseModel):
    """Payload sent to the policy engine to evaluate a proposed RL action."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    proposed_action: RLAction = Field(...)
    current_state: RLState = Field(...)
    autonomy_mode: Literal[0, 1, 2, 3, 4, 5] = Field(...)
    requester_id: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("autonomy_mode")
    @classmethod
    def validate_autonomy_level(cls, v: int) -> int:
        if v < 0 or v > 5:
            raise ValueError("Autonomy mode must be between 0 and 5")
        return v


class PolicyDecisionModel(BaseModel):
    """Decision returned from the policy/governance engine after evaluation."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    approved: bool = Field(...)
    modified_action: Optional[RLAction] = Field(default=None)
    reason: str = Field(..., min_length=1)
    severity_override: Optional[Literal["low", "medium", "high", "critical"]] = None
    escalate_to_human: bool = Field(default=False)
    audit_event_id: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def check_consistency(self) -> "PolicyDecisionModel":
        if not self.approved and self.modified_action is not None:
            raise ValueError("modified_action should only be set when approved=True")
        if self.escalate_to_human and self.approved:
            raise ValueError("Cannot both approve and escalate to human simultaneously")
        return self


class PolicyAuditModel(BaseModel):
    """Base Pydantic model for policy enforcement audit logs."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    incident_id: Optional[UUID] = Field(
        None, description="Incident this action relates to (if any)"
    )
    action_taken: str = Field(
        ..., description="Description of the action (e.g. 'port disable')"
    )
    executed_by: Literal["human", "autonomous", "policy_engine"] = Field(...)
    approved_by: Optional[str] = Field(default=None)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)


class PolicyAuditCreateModel(PolicyAuditModel):
    """Fields when logging a new policy enforcement action."""

    timestamp: datetime = Field(
        ...,
        description="When the action occurred (UTC)",
    )


class PolicyAuditReadModel(PolicyAuditModel):
    """Read representation of a policy audit entry."""

    id: UUID = Field(...)
    timestamp: datetime
    created_at: datetime
    updated_at: datetime


class PolicyAuditRecord(Base):
    """Persistent audit log for all automated or approved policy actions."""

    __tablename__ = "policy_audits"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True,
    )
    incident_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_taken: Mapped[str] = mapped_column(Text, nullable=False)
    executed_by: Mapped[str] = mapped_column(String(50), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Optional relationship (for easier querying if needed)
    incident: Mapped[Optional["IncidentRecord"]] = relationship(
        "IncidentRecord", back_populates="policy_audits", uselist=False
    )

    __table_args__ = (
        Index("ix_policy_audits_incident_id", "incident_id"),
        Index("ix_policy_audits_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<PolicyAuditRecord id={self.id} action={self.action_taken} success={self.success}>"


__all__ = [
    # Runtime policy evaluation
    "PolicyCheckRequestModel",
    "PolicyDecisionModel",
    # Audit logging
    "PolicyAuditModel",
    "PolicyAuditCreateModel",
    "PolicyAuditReadModel",
    "PolicyAuditRecord",
]
