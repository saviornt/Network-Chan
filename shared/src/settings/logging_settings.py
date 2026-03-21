"""Dedicated Pydantic Settings for logging configuration in Network-Chan.

Handles log level, destination, file path, rotation policy, and backup retention.
Environment variables are prefixed with LOGGING__ (double underscore).

Example:
    export LOGGING__LEVEL=DEBUG
    export LOGGING__DESTINATION=both
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class LoggingSettings(BaseSettings):
    """
    Configuration for structured logging behavior across the application.

    Controls log level, output destination (stdout/file/both), file path,
    rotation timing, and how many backup files to retain.

    Environment variables use the LOGGING__ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="LOGGING__",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        env_ignore_empty=True,
        env_nested_delimiter="__",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Global logging level for the application.",
    )
    destination: Literal["stdout", "file", "both"] = Field(
        default="stdout",
        description=(
            "Where logs should be sent. "
            "'stdout' → console/terminal only, "
            "'file' → log file only, "
            "'both' → console + file."
        ),
    )
    file_path: Path = Field(
        default=Path("logs/network-chan.log"),
        description=(
            "Path to the primary log file (relative to data_dir if not absolute). "
            "Only used when destination is 'file' or 'both'. "
            "Parent directories are auto-created."
        ),
    )
    rotation_when: Literal["midnight", "D", "H"] = Field(
        default="midnight",
        description=(
            "Log file rotation policy. "
            "'midnight' → rotate at midnight each day, "
            "'D' → daily rotation, "
            "'H' → hourly rotation."
        ),
    )
    backup_count: int = Field(
        default=7,
        ge=0,
        description=(
            "Number of rotated backup log files to retain. "
            "Oldest files are deleted when this limit is exceeded. "
            "0 = keep forever (not recommended on resource-constrained devices)."
        ),
    )


# Singleton instance — import and use directly
logging_settings: LoggingSettings = LoggingSettings()

__all__ = [
    "LoggingSettings",
    "logging_settings",
]
