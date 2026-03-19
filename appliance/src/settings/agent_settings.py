"""Agent-specific settings for the Appliance Q-Learning component.

Loaded from environment variables with prefix AGENT_.
Example: AGENT_ROLLING_WINDOW=200
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Settings specific to the Appliance Q-Learning agent."""

    rolling_window: int = Field(
        default=100,
        ge=10,
        description="Number of recent episodes for rolling averages (TD error & reward)",
    )
    checkpoint_interval: int = Field(
        default=50,
        ge=1,
        description="Save checkpoint every N episodes",
    )
    checkpoint_path: str = Field(
        default="checkpoints/tabular_q_latest.npz",
        description="Relative path for latest checkpoint",
    )
    max_steps_per_episode: int = Field(
        default=200,
        ge=10,
        description="Default max steps before forcing episode end",
    )

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
