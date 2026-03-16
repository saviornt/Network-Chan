"""Reinforcement learning state and action models."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import NetworkChanBaseModel
from .telemetry import FeatureVector


class RLState(NetworkChanBaseModel):
    """Current observed state for RL agent decision making."""

    device_id: str
    features: FeatureVector
    previous_action: RLAction | None = None
    reward: float = Field(ge=-10, le=10, default=0.0)  # tunable range
    episode_step: int = Field(ge=0)


class RLAction(NetworkChanBaseModel):
    """Action proposed by the edge RL agent."""

    action_type: Literal[
        "change_channel",
        "reassign_client",
        "throttle_bandwidth",
        "reboot_ap",
        "reset_interface",
    ]
    target: str = Field(min_length=1, description="Device/interface/client target")
    parameters: dict[str, str | int | float] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1, default=0.95)
    estimated_reward: float = Field(default=0.0)
