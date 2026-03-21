"""Pydantic models for core Q-Learning data structures.

This module defines validated shapes for transitions, episode statistics,
checkpoint metadata, and related Q-Learning artifacts.

These are used across edge (Appliance), central (Assistant), and simulation code
for consistency. No ORM or FAISS storage is required here — these are transient
or buffer/checkpoint data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransitionModel(BaseModel):
    """A single step in an agent's trajectory (experience tuple).

    Atomic unit stored in replay buffers and used for Q-value updates.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        # frozen=True,  # Uncomment if transitions should be immutable after creation
    )

    state: Any = Field(
        ...,
        description=(
            "Current state representation. "
            "Can be int (tabular), np.ndarray, list, or torch.Tensor (function approx)."
        ),
    )
    action: int = Field(
        ...,
        ge=0,
        description="Index of the action taken",
    )
    reward: float = Field(
        ...,
        description="Scalar reward received after action",
    )
    next_state: Any = Field(
        ...,
        description="Resulting state after action (same type as state)",
    )
    done: bool = Field(
        ...,
        description="True if this transition ended the episode",
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="When this transition was collected (UTC)",
    )

    @field_validator("state", "next_state", mode="before")
    @classmethod
    def normalize_state(cls, v: Any) -> Any:
        """Coerce common types (e.g. tuple → list) for consistency in buffers."""
        if isinstance(v, tuple):
            return list(v)
        return v


class EpisodeStatsModel(BaseModel):
    """Summary statistics for a complete episode / rollout."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
    )

    episode_id: str = Field(
        ...,
        description="Unique identifier for this episode (e.g. UUID string)",
    )
    total_reward: float = Field(
        ...,
        description="Sum of rewards over the episode",
    )
    length: int = Field(
        ...,
        ge=0,
        description="Number of steps in the episode",
    )
    avg_reward: float = Field(
        ...,
        description="Mean reward per step",
    )
    final_epsilon: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Exploration rate (epsilon) at episode end",
    )
    start_time: datetime = Field(
        ...,
        description="UTC start timestamp of the episode",
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="UTC end timestamp (None if episode is ongoing)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional extra info (e.g. device_id, network conditions, agent version)",
    )


__all__ = [
    "TransitionModel",
    "EpisodeStatsModel",
]
