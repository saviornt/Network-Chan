"""Pydantic Settings for Q-Learning hyperparameters and runtime configuration.

This module defines the settings that are loaded from environment variables,
with sensible defaults. It uses Pydantic Settings (v2) for type-safe,
validated configuration.

All settings can be overridden via environment variables with the prefix
`QLEARN_` (configurable via model_config).
"""

from __future__ import annotations

from functools import cached_property
from typing import Annotated, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Reusable constraint aliases (for readability and reuse)
PositiveFloat = Annotated[float, Field(gt=0.0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
StrictlyPositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class QLearningSettings(BaseSettings):
    """Core settings for the Q-Learning component.

    Loaded from environment variables with prefix QLEARN_.
    Example: QLEARN_ALPHA=0.15 sets alpha to 0.15.
    """

    # Learning parameters
    alpha: Probability = Field(
        default=0.1,
        description="Learning rate — how much new information overrides old",
    )
    gamma: Probability = Field(
        default=0.99,
        description="Discount factor for future rewards",
    )

    # Exploration schedule
    epsilon_start: Probability = Field(
        default=0.3,
        description="Initial exploration probability",
    )
    epsilon_min: Probability = Field(
        default=0.01,
        description="Minimum exploration probability",
    )
    epsilon_decay: Probability = Field(
        default=0.995,
        description="Per-step/episode decay factor (multiplicative)",
    )

    # Replay & training behavior
    min_replay_size: NonNegativeInt = Field(
        default=100,
        description="Minimum number of transitions before training starts",
    )
    batch_size: StrictlyPositiveInt = Field(
        default=32,
        description="Batch size for updates (used in central trainer)",
    )

    # Tabular-specific defaults (can be overridden per instance)
    default_n_states: StrictlyPositiveInt = Field(
        default=256,
        description="Default number of discrete states (for tabular)",
    )
    default_n_actions: StrictlyPositiveInt = Field(
        default=4,
        description="Default number of discrete actions (for tabular)",
    )

    # Runtime behavior flags
    mode: Literal["train", "eval", "collect"] = Field(
        default="train",
        description="Runtime mode: train (learn), eval (exploit), collect (gather data only)",
    )

    model_config = SettingsConfigDict(
        env_prefix="QLEARN_",
        env_file=".env",  # optional: loads from .env if present
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown env vars
        case_sensitive=False,
    )

    @cached_property
    def epsilon_current(self) -> float:
        """Current exploration rate (starts at epsilon_start)."""
        return self.epsilon_start

    def decay_epsilon(self) -> None:
        """Apply one step of epsilon decay (in-place)."""
        self.epsilon_current = max(
            self.epsilon_min, self.epsilon_current * self.epsilon_decay
        )
