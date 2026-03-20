"""Core Pydantic schemas and SQLAlchemy ORM records for the reinforcement learning domain.

This module defines the general-purpose RL building blocks (observations, states, actions, rewards)
and model registry for versioning/tracking trained models/checkpoints.

Q-Learning-specific structures (e.g. tabular Q-tables, epsilon tracking) are in q_learning_models.py.
"""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from sqlalchemy import DateTime, String, JSON, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.src.models.sqlite_models import Base


class RLObservation(BaseModel):
    """A single observation / feature vector from the network environment.

    Raw input to RL agents (Q-Learning, REPTILE, GNNs, etc.).
    """

    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
        json_encoders={np.ndarray: lambda v: v.tolist()},
    )

    features: List[float] = Field(
        ...,
        min_length=1,
        description="Flattened feature vector (latency, packet loss, client count, etc.)",
    )
    original_shape: Tuple[int, ...] = Field(
        default=(0,),
        description="Original shape before flattening (for GNN/CNN agents)",
    )
    device_id: str = Field(
        ..., min_length=1, description="Originating device identifier"
    )
    timestamp: float = Field(..., gt=0, description="Unix timestamp (seconds)")

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError("Features cannot be empty")
        if any(np.isnan(x) or np.isinf(x) for x in v):
            raise ValueError("Features contain NaN or Inf")
        return v

    def to_numpy(self) -> np.ndarray:
        arr = np.array(self.features, dtype=np.float32)
        if self.original_shape != (0,):
            arr = arr.reshape(self.original_shape)
        return arr


class RLState(BaseModel):
    """Full agent state at a timestep (observation + optional internal state)."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    observation: RLObservation = Field(...)
    internal_state: Optional[Any] = Field(
        default=None,
        description="Agent-specific internal state (LSTM hidden, traces, etc.)",
    )
    episode_step: int = Field(default=0, ge=0, description="Step in current episode")
    episode_id: Optional[str] = Field(default=None, description="Episode identifier")


class RLAction(BaseModel):
    """Action proposed or taken by an RL agent."""

    model_config = ConfigDict(extra="forbid")

    action_type: str = Field(
        ..., min_length=1, description="Semantic type (e.g. 'change_channel')"
    )
    target: Optional[str] = Field(default=None, description="Target identifier")
    value: Any = Field(..., description="Action parameter (int, float, dict, etc.)")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Agent confidence"
    )
    proposed_at: float = Field(..., gt=0, description="Unix timestamp when proposed")


class RewardSignal(BaseModel):
    """Reward signal received after executing an action."""

    model_config = ConfigDict(extra="forbid")

    value: float = Field(..., description="Scalar reward (higher is better)")
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of reward sources (e.g. latency improvement, energy cost)",
    )
    timestamp: float = Field(..., gt=0, description="Unix timestamp when computed")


class ModelRegistryRecord(Base):
    """Persistent SQLite table tracking versions of trained ML/RL models."""

    __tablename__ = "model_registry"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trained_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    model_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    performance_metrics: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )

    __table_args__ = (
        Index(
            "ix_model_registry_model_name_version", "model_name", "version", unique=True
        ),
    )

    def __repr__(self) -> str:
        return f"<ModelRegistryRecord {self.model_name} v{self.version}>"


class ModelRegistryModel(BaseModel):
    """Base fields shared across ModelRegistry Pydantic schemas."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="Name/identifier of the model")
    version: str = Field(..., description="Semantic version or commit hash")
    model_type: Literal["tinyml", "q_learning", "gnn", "rl_maml", "other"]
    description: Optional[str] = None
    trained_on: Optional[datetime] = None
    performance_metrics: Dict[str, float] = Field(default_factory=dict)


class ModelRegistryCreateModel(ModelRegistryModel):
    """Fields required when registering a new model version."""

    model_hash: str = Field(
        ..., description="Content hash (sha256) of serialized model"
    )
    file_path: Optional[str] = Field(
        None, description="Path to model file if stored locally"
    )


class ModelRegistryReadModel(ModelRegistryModel):
    """Read representation of a model registry entry."""

    id: UUID
    model_hash: str
    file_path: Optional[str]
    created_at: datetime
    updated_at: datetime


__all__ = [
    # Core RL
    "RLObservation",
    "RLState",
    "RLAction",
    "RewardSignal",
    # Model registry
    "ModelRegistryModel",
    "ModelRegistryCreateModel",
    "ModelRegistryReadModel",
    "ModelRegistryRecord",
]
