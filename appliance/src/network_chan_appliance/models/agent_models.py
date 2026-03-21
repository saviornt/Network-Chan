"""Agent-specific models for the Appliance Q-Learning component.

These extend the shared models with edge-specific stats and observability fields.
"""

from datetime import datetime, timezone

from pydantic import Field

from shared.models.q_learning_models import EpisodeStats


class AgentEpisodeStats(EpisodeStats):
    """Extended episode statistics with edge-specific rolling metrics."""

    rolling_avg_td_error: float = Field(
        default=0.0,
        description="Rolling average TD error over the last N episodes",
    )
    rolling_avg_reward: float = Field(
        default=0.0,
        description="Rolling average reward over the last N episodes",
    )
    max_abs_td_error_this_episode: float = Field(
        default=0.0,
        description="Maximum absolute TD error in this episode",
    )
    mean_td_error_this_episode: float = Field(
        default=0.0,
        description="Mean TD error in this episode",
    )
    checkpoint_saved: bool = Field(
        default=False,
        description="Whether a checkpoint was saved at the end of this episode",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when episode stats were finalized",
    )
