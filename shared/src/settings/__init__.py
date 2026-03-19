"""Settings package for Network-Chan — central hub for all configuration/settings modules.

This package provides modular, Pydantic-v2 validated settings classes that are loaded
from environment variables and .env files. Each settings module is responsible for
a specific concern (environment, governance, paths, RL, logging, etc.) to enforce
separation of concerns and improve maintainability.

Exported singletons are the primary way to access configuration throughout the
application. Import them directly from this package for clean, consistent usage.

Key principles:
- Pydantic SettingsConfigDict with appropriate env_prefix per module
- Structured logging on load/validation where appropriate
- Type-safe fields and validators
- Singleton instances for global access
- No runtime side-effects except logging and directory creation (where needed)

Typical usage:
    from shared.src.settings import (
        environment_settings,
        governance_settings,
        # ... other modules as added
    )

    if environment_settings.is_production:
        logger.info("Running in production mode")

    if governance_settings.autonomous_mode >= AutonomyLevel.AUTONOMOUS:
        # dashboard or policy engine will handle warnings
        ...

Public exports:
    - environment_settings: EnvironmentSettings singleton
    - governance_settings: GovernanceSettings singleton
    - AutonomyLevel: Enum for autonomy modes
    - (additional modules/singletons added as settings are split)

See Also:
    - Each submodule's docstring for detailed field descriptions
    - logging_factory.py for how settings interact with structured logging
"""

from .auth_settings import (
    auth_settings,
    AuthSettings,
)
from .environment_settings import (
    environment_settings,
    EnvironmentSettings,
)
from .faiss_settings import (
    faiss_settings,
    FaissSettings,
)
from .governance_settings import (
    governance_settings,
    GovernanceSettings,
    AutonomyLevel,
)
from .logging_settings import logging_settings, LoggingSettings
from .mqtt_settings import mqtt_settings, MqttSettings
from .q_learning_settings import q_learning_settings, QLearningSettings
from .retry_settings import retry_settings, RetrySettings
from .sqlite_settings import sqlite_settings, SQLiteSettings


__all__ = [
    # Singletons
    "auth_settings",
    "environment_settings",
    "faiss_settings",
    "governance_settings",
    "logging_settings",
    "mqtt_settings",
    "q_learning_settings",
    "retry_settings",
    "sqlite_settings",
    # Classes & Enums
    "AuthSettings",
    "EnvironmentSettings",
    "FaissSettings",
    "GovernanceSettings",
    "AutonomyLevel",
    "LoggingSettings",
    "MqttSettings",
    "QLearningSettings",
    "RetrySettings",
    "SQLiteSettings",
]
