"""Core models for the reinforcement learning domain in Network-Chan.

This module defines the canonical data structures for RL observations,
states, actions, and rewards. These models are used across the entire
project (Appliance edge inference, Assistant central training, simulation,
multi-agent coordination, etc.) to ensure consistency and type safety.

All models inherit from RLBaseModel with strict validation rules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CheckpointSource(str, Enum):
    EDGE = "edge"
    CENTRAL = "central"
    SIMULATION = "simulation"


class RLBaseModel(BaseModel):
    """Base Pydantic model for all reinforcement learning domain objects.

    Enforces strict validation, forbids extra fields, and supports safe
    coercion where explicitly allowed. Designed for use in both low-latency
    edge (Raspberry Pi Appliance) and compute-heavy central (Assistant) contexts.
    """

    model_config = ConfigDict(
        strict=True,  # No unexpected type coercion
        extra="forbid",  # Reject unknown fields
        frozen=False,  # Allow mutation when needed (e.g. updating stats)
        validate_assignment=True,  # Re-validate when attributes are set
        populate_by_name=True,  # Allow population by field name or alias
        arbitrary_types_allowed=True,  # Support NumPy arrays, torch tensors, etc.
        json_encoders={np.ndarray: lambda v: v.tolist()},  # Safe NumPy serialization
    )


class RLObservation(RLBaseModel):
    """A single observation / feature vector from the network environment.

    This is the raw input fed to RL agents (Q-Learning, REPTILE, GNNs, etc.).
    Contains the flattened feature vector plus metadata for traceability and
    reconstruction (e.g. for GNN topology-aware processing).
    """

    features: List[float] = Field(
        ...,
        description="Flattened feature vector (e.g. latency, packet loss, client count, noise floor, ...)",
        min_length=1,
    )
    original_shape: Tuple[int, ...] = Field(
        default=(0,),
        description="Original shape before flattening (for later reshaping in GNN/CNN agents)",
    )
    device_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the originating device (e.g. AP name, switch IP, MAC)",
    )
    timestamp: float = Field(
        ...,
        gt=0,
        description="Unix timestamp (seconds) when observation was collected",
    )

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: List[float]) -> List[float]:
        """Ensure features are valid (non-empty, finite values)."""
        if not v:
            raise ValueError("Observation features cannot be empty")
        if any(np.isnan(x) or np.isinf(x) for x in v):
            raise ValueError("Features contain NaN or Inf values")
        return v

    def to_numpy(self) -> np.ndarray:
        """Convert features to a NumPy array (edge-friendly, float32)."""
        arr = np.array(self.features, dtype=np.float32)
        if self.original_shape != (0,):
            arr = arr.reshape(self.original_shape)
        return arr


class RLState(RLBaseModel):
    """The full state of an RL agent at a given timestep.

    Combines the current observation with optional internal agent state
    (e.g. previous action, eligibility traces, LSTM hidden state, etc.).
    Used by agents that maintain memory or recurrent context.
    """

    observation: RLObservation = Field(
        ...,
        description="Current environment observation",
    )
    internal_state: Optional[Any] = Field(
        default=None,
        description=(
            "Agent-specific internal state (e.g. LSTM hidden, eligibility traces, "
            "previous action). Type depends on agent architecture."
        ),
    )
    episode_step: int = Field(
        default=0,
        ge=0,
        description="Step count within the current episode",
    )
    episode_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the current episode",
    )


class RLAction(RLBaseModel):
    """Action proposed or taken by an RL agent.

    Structured representation of discrete or continuous actions with
    metadata for auditing, safety gating, and rollback.
    """

    action_type: str = Field(
        ...,
        min_length=1,
        description="Semantic type (e.g. 'change_channel', 'throttle_client', 'rebalance_load')",
    )
    target: Optional[str] = Field(
        default=None,
        description="Target identifier (AP name, client MAC, port ID, etc.)",
    )
    value: Any = Field(
        ...,
        description="Action parameter (int for discrete, float for continuous, dict for complex)",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Agent confidence score (used for safety gating)",
    )
    proposed_at: float = Field(
        ...,
        gt=0,
        description="Unix timestamp when action was proposed",
    )


class RewardSignal(RLBaseModel):
    """Reward signal received after executing an action.

    Scalar value plus optional component breakdown for explainability,
    debugging, and reward shaping analysis.
    """

    value: float = Field(
        ...,
        description="Scalar reward (higher is better)",
    )
    components: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Breakdown of reward sources (e.g. {'latency_improvement': 0.3, "
            "'loss_reduction': 0.15, 'energy_savings': -0.05})"
        ),
    )
    timestamp: float = Field(
        ...,
        gt=0,
        description="Unix timestamp when reward was computed",
    )


class TabularQCheckpointMetadata(BaseModel):
    """Metadata stored alongside a saved tabular Q-table checkpoint."""

    created_at: datetime = Field(..., description="When this checkpoint was saved")
    episode_count: int = Field(
        ..., ge=0, description="Total episodes experienced so far"
    )
    total_steps: int = Field(..., ge=0, description="Cumulative training steps")
    avg_reward_last_100: Optional[float] = Field(
        None, description="Rolling average reward over last 100 episodes"
    )
    epsilon: float = Field(
        ..., ge=0.0, le=1.0, description="Exploration rate at save time"
    )
    source: CheckpointSource = Field(
        ..., description="Where this checkpoint was generated"
    )
    version: str = Field(
        default="1.0",
        description="Checkpoint format version (for future migrations)",
    )
    extra_tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary key-value tags (e.g. {'network_id': 'home-lab-1'})",
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="Reason this is a fallback checkpoint (e.g. 'file_missing', 'corrupt_metadata')",
    )
    rolling_avg_td_error: Optional[float] = Field(
        default=None,
        description="Rolling average TD error over recent episodes",
    )


class Checkpoint(BaseModel):
    """Full checkpoint structure (metadata + serialized Q data).

    Used for save/load round-trips between edge and central.
    """

    metadata: TabularQCheckpointMetadata
    q_table: Union[List[List[float]], Dict[str, Any]] = (
        Field(  # numpy serialized as list-of-lists or dict
            ...,
            description="Serialized Q-table (tabular: 2D list; future: other formats)",
        )
    )
