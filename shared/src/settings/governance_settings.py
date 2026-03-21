"""Governance and safety policy settings for Network-Chan.

Extracted from shared_settings.py to enforce separation of concerns.
Contains autonomy levels, rate limits, approval thresholds, and related validators.

Loaded via Pydantic Settings from .env / .env.local with GOV_ prefix.
Singleton instance available as `governance_settings`.

See Also:
    - vision.md, security_design.md, technical_requirements.md for level definitions
"""

from __future__ import annotations

from enum import IntEnum
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.utils.logging_factory import get_logger

logger = get_logger("governance_settings", category="settings")


class AutonomyLevel(IntEnum):
    """Autonomy levels aligned with project vision and security design.

    Lower levels prioritize safety/manual oversight; higher levels enable more automation.
    Stored as integer in environment variables for simplicity, but exposed as enum for type safety.

    Levels:
        0 - OBSERVER: Monitor & log only — no suggestions or actions
        1 - ADVISOR: Suggest actions via dashboard/LLM
        2 - SUPERVISED: Suggest + require approval for most actions
        3 - SEMI_AUTONOMOUS: Auto-execute safe/low-risk actions
        4 - AUTONOMOUS: Full self-healing with rollback guardrails
        5 - EXPERIMENTAL: Bleeding-edge/research mode — no safety nets
    """

    OBSERVER = 0
    ADVISOR = 1
    SUPERVISED = 2
    SEMI_AUTONOMOUS = 3
    AUTONOMOUS = 4
    EXPERIMENTAL = 5


class GovernanceSettings(BaseSettings):
    """Governance and safety policy settings — controls autonomy, rate limits, approvals.

    Loaded from environment variables with GOV_ prefix (e.g. GOV_AUTONOMOUS_MODE=3).
    Singleton instance: `from shared.settings.governance_settings import governance_settings`

    Safety invariants are enforced via model validators.
    """

    model_config = SettingsConfigDict(
        env_prefix="GOV_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",  # Prevent typos / unknown env vars
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    autonomous_mode: AutonomyLevel = Field(
        default=AutonomyLevel.SEMI_AUTONOMOUS,
        description="Current autonomy level (0=Observer → 5=Experimental)",
    )
    max_reboots_per_hour: int = Field(
        default=1,
        ge=0,
        le=10,
        description="Maximum device reboots allowed per hour (safety throttle)",
    )
    max_channel_changes_per_10min: int = Field(
        default=2,
        ge=0,
        le=20,
        description="Maximum Wi-Fi channel changes allowed per 10 minutes",
    )
    require_approval_above_level: AutonomyLevel = Field(
        default=AutonomyLevel.AUTONOMOUS,
        description="Actions requiring explicit human approval when autonomy >= this level",
    )

    @model_validator(mode="after")
    def validate_rate_limits(self) -> Self:
        """Basic sanity checks on rate-limit fields.

        Returns:
            Self: Validated settings instance
        """
        if (
            self.max_reboots_per_hour == 0
            and self.autonomous_mode >= AutonomyLevel.SEMI_AUTONOMOUS
        ):
            logger.warning(
                "Reboots disabled while semi-autonomous or higher — remediation may be limited",
                max_reboots_per_hour=self.max_reboots_per_hour,
            )
        return self


# Singleton instance — import and use directly
governance_settings: GovernanceSettings = GovernanceSettings()


__all__ = [
    "GovernanceSettings",
    "governance_settings",
    "AutonomyLevel",
]
