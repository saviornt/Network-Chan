"""Environment and runtime-mode settings for Network-Chan.

This module manages the current execution environment (development, staging, production)
and related flags that affect behavior, logging verbosity, safety strictness, etc.

Loaded via Pydantic Settings from .env / .env.local with ENV_ prefix.
Singleton instance available as `environment_settings`.

See Also:
    - vision.md: environment considerations
    - development_coding_standards.md: environment-aware patterns
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.utils.logging_factory import get_logger


logger = get_logger("environment_settings", category="settings")


class EnvironmentSettings(BaseSettings):
    """Runtime environment configuration — controls dev/staging/prod behavior.

    Loaded from environment variables with ENV_ prefix (e.g. ENV_APP_ENV=production).
    Singleton instance: `from shared.settings.environment_settings import environment_settings`

    This is the single source of truth for environment detection across the project.
    """

    model_config = SettingsConfigDict(
        env_prefix="ENV_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",  # Prevent typos / unknown env vars
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description=(
            "Current runtime environment. "
            "Affects logging verbosity, safety checks, feature availability, "
            "and debug behavior throughout the application."
        ),
    )

    @model_validator(mode="after")
    def log_environment_on_load(self) -> Self:
        """Log the loaded environment on initialization (observability)."""
        logger.info(
            "Environment settings loaded",
            app_env=self.app_env,
            is_development=self.is_development,
            is_production=self.is_production,
        )
        return self

    @property
    def is_development(self) -> bool:
        """Helper: True if running in development mode."""
        return self.app_env == "development"

    @property
    def is_staging(self) -> bool:
        """Helper: True if running in staging mode."""
        return self.app_env == "staging"

    @property
    def is_production(self) -> bool:
        """Helper: True if running in production mode."""
        return self.app_env == "production"

    @property
    def is_safe_mode(self) -> bool:
        """Helper: True if environment should enforce stricter safety rules.

        Currently equivalent to production, but can be decoupled later.
        """
        return self.is_production

    # Future extension points:
    # debug_mode: bool = Field(default=False)
    # enable_experimental_features: bool = Field(default=False)


# Singleton instance — import and use directly
environment_settings: EnvironmentSettings = EnvironmentSettings()


__all__ = [
    "EnvironmentSettings",
    "environment_settings",
]
