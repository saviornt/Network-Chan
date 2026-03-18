"""Pydantic models related to policy checks, autonomy modes, and remediation decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .base_model import NetworkChanBaseModel
from .rl_model import RLAction, RLState


class PolicyCheckRequest(NetworkChanBaseModel):
    """Payload sent to the policy engine when evaluating a proposed action."""

    proposed_action: RLAction
    current_state: RLState
    autonomy_mode: Literal[0, 1, 2, 3, 4, 5] = Field(
        ..., description="0=Observer → 5=Experimental"
    )
    requester_id: str | None = Field(
        default=None, description="User or system ID requesting the action"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("autonomy_mode")
    @classmethod
    def validate_autonomy_level(cls, v: int) -> int:
        if v < 0 or v > 5:
            raise ValueError("Autonomy mode must be between 0 and 5")
        return v


class PolicyDecision(NetworkChanBaseModel):
    """Response from the policy/governance layer after evaluating a request."""

    approved: bool = Field(
        description="Whether the action is allowed to execute immediately"
    )
    modified_action: RLAction | None = Field(
        default=None,
        description="Potentially altered action (e.g. throttle instead of reboot)",
    )
    reason: str = Field(min_length=1, description="Human-readable explanation")
    severity_override: Literal["low", "medium", "high", "critical"] | None = None
    escalate_to_human: bool = Field(default=False)
    audit_event_id: str | None = Field(
        default=None, description="Reference to created audit log entry"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def check_consistency(self) -> PolicyDecision:
        if not self.approved and self.modified_action is not None:
            raise ValueError("modified_action should only be set when approved=True")
        if self.escalate_to_human and self.approved:
            raise ValueError("Cannot both approve and escalate to human simultaneously")
        return self
