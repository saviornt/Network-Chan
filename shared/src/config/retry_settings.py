"""Dedicated Pydantic Settings for retry behavior on transient failures.

This module provides retry configuration for network / I/O operations.
Environment variables are prefixed with RETRY__ (double underscore).

Example:
    export RETRY__MAX_ATTEMPTS=8
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetrySettings(BaseSettings):
    """
    Configuration parameters for retrying transient failures (timeouts, connection errors, etc.).

    All fields use the RETRY__ env prefix (thanks to env_nested_delimiter="__" in base).
    """

    model_config = SettingsConfigDict(
        env_prefix="RETRY__",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    max_attempts: int = Field(
        default=5,
        ge=1,
        le=12,
        description=(
            "Maximum number of retry attempts before raising NetworkExhaustedError. "
            "Typical values: 3–8 for most network operations."
        ),
    )
    min_wait_sec: float = Field(
        default=1.0,
        ge=0.1,
        description="Minimum delay between retry attempts (seconds).",
    )
    max_wait_sec: float = Field(
        default=30.0,
        ge=1.0,
        description="Maximum delay — exponential backoff caps here (seconds).",
    )
    jitter_sec: float = Field(
        default=0.5,
        ge=0.0,
        description=(
            "Maximum random jitter added to each wait interval to prevent thundering-herd "
            "effects (seconds)."
        ),
    )

    # Optional: you could add more fields later, e.g.
    # multiplier: float = Field(default=1.0, description="Exponential backoff multiplier")


# Singleton instance — import and use directly
retry_settings: RetrySettings = RetrySettings()
