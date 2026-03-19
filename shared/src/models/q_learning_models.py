"""Pydantic models for core Q-Learning data structures.

This module defines the validated data shapes used across the Q-Learning
component: transitions, episode statistics, checkpoint metadata, etc.

All models use Pydantic v2 with strict typing, validation, and serialization
support. They are shared between edge (Appliance), central (Assistant), and
simulation code to ensure consistency.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class Transition(BaseModel):
    """A single step in an agent's trajectory (experience tuple).

    This is the atomic unit stored in replay buffers and used for updates.
    """

    state: Any = Field(
        ...,
        description=(
            "Current state representation. "
            "Can be int (tabular), np.ndarray, list, or torch.Tensor (function approx)."
        ),
    )
    action: int = Field(..., ge=0, description="Index of the action taken")
    reward: float = Field(..., description="Scalar reward received after action")
    next_state: Any = Field(
        ...,
        description="Resulting state after action (same type as state)",
    )
    done: bool = Field(..., description="True if this transition ended the episode")
    timestamp: Optional[datetime] = Field(
        default=None,
        description="When this transition was collected (UTC)",
    )

    @field_validator("state", "next_state", mode="before")
    @classmethod
    def normalize_state(cls, v: Any) -> Any:
        """Optional: coerce common types (e.g. tuple → list) for consistency."""
        if isinstance(v, tuple):
            return list(v)
        return v


class EpisodeStats(BaseModel):
    """Summary statistics for a complete episode / rollout."""

    episode_id: str = Field(..., description="Unique identifier for this episode")
    total_reward: float = Field(..., description="Sum of rewards over the episode")
    length: int = Field(..., ge=0, description="Number of steps in the episode")
    avg_reward: float = Field(..., description="Mean reward per step")
    final_epsilon: float = Field(
        ..., ge=0.0, le=1.0, description="Exploration rate at episode end"
    )
    start_time: datetime = Field(..., description="UTC start timestamp")
    end_time: Optional[datetime] = Field(
        None, description="UTC end timestamp (if completed)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional extra info (e.g. device_id, network conditions)",
    )
