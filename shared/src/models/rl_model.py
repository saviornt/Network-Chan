"""Reinforcement Learning domain models.

Defines the core data structures for RL states, actions, and rewards.
Validated with Pydantic v2 for type safety and serialization.
Used by both edge inference (Appliance) and central training (Assistant).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from pydantic import Field, field_validator

from .base_model import MLBaseModel  # assuming you have a base in models/base.py


class RLObservation(MLBaseModel):
    """Current network observation / state vector for RL agents.

    Represents the flattened feature vector fed into Q-Learning, REPTILE,
    or GNN embedding steps. Includes metadata for traceability.
    """

    features: List[float] = Field(
        ...,
        description="Flattened feature vector (e.g. latency, loss, clients, noise, ...)",
    )
    original_shape: Tuple[int, ...] = Field(
        default=(0,),
        description="Original shape before flattening (for reshape in GNNs)",
    )
    device_id: str = Field(
        ..., min_length=1, description="Originating device identifier"
    )
    timestamp: float = Field(..., gt=0, description="Unix timestamp in seconds")

    @field_validator("features")
    @classmethod
    def validate_features_non_empty(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError("Observation features cannot be empty")
        if any(np.isnan(x) or np.isinf(x) for x in v):
            raise ValueError("Features contain NaN or Inf values")
        return v

    def to_numpy(self) -> np.ndarray:
        """Convert features to NumPy array (edge-friendly)."""
        arr = np.array(self.features, dtype=np.float32)
        if self.original_shape != (0,):
            arr = arr.reshape(self.original_shape)
        return arr


class RLAction(MLBaseModel):
    """Action proposed by an RL agent.

    Can be discrete (e.g. channel index) or continuous (e.g. throttle percentage).
    Includes confidence and metadata for auditing/rollback.
    """

    action_type: str = Field(
        ..., min_length=1, description="Type like 'change_channel', 'throttle_client'"
    )
    target: str | None = Field(
        default=None, description="Target identifier (AP name, client MAC, etc.)"
    )
    value: Any = Field(..., description="Action parameter (int/float/str)")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Model confidence score"
    )
    proposed_at: float = Field(..., gt=0, description="Unix timestamp when proposed")


class RewardSignal(MLBaseModel):
    """Reward signal received after executing an action.

    Scalar value + optional breakdown for explainability.
    Used in Q-update, REPTILE adaptation, or multi-agent consensus.
    """

    value: float = Field(..., description="Scalar reward (higher = better)")
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown e.g. {'latency_improvement': 0.3, 'loss_reduction': 0.15}",
    )
    timestamp: float = Field(
        ..., gt=0, description="Unix timestamp when reward computed"
    )
