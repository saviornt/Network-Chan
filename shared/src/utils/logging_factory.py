"""Structured logging factory for Network-Chan using structlog + stdlib integration.

Features:
- Dynamic log level from shared_settings.log_level (respected at runtime)
- Colored console in development, JSON lines in production
- Automatic context binding + Pi/edge detection
- Thread-safe and async-friendly

Usage:
    from src.utils.logging_factory import get_logger

    logger = get_logger("telemetry", device_id="ap-01")
    logger.info("Starting poll cycle", interval_s=30)
"""

from __future__ import annotations

import logging
import sys
from typing import Any
from pathlib import Path

import structlog
from logging.handlers import TimedRotatingFileHandler
from pydantic import BaseModel, ConfigDict, field_validator

from shared.src.config.logging_settings import logging_settings
from shared.src.config.shared_settings import shared_settings


class LogContext(BaseModel):
    """Pydantic-validated context for structured log entries."""

    model_config = ConfigDict(extra="allow", frozen=False)

    component: str | None = None
    autonomy_mode: str | None = None
    device_id: str | None = None
    incident_id: str | None = None
    edge: bool = False
    request_id: str | None = None

    @field_validator("autonomy_mode", mode="before")
    @classmethod
    def normalize_autonomy(cls, v: Any) -> str | None:
        return str(v).upper() if v is not None else None


class StructuredLogging:
    """Central factory for structured loggers with rotation support."""

    _configured: bool = False

    @classmethod
    def configure(cls) -> None:
        """Configure structlog globally (idempotent).

        Sets log level from shared_settings and selects renderer
        based on environment/TTY status.
        """
        if cls._configured:
            return

        # Map string level → logging integer constant
        level_map: dict[str, Any] = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        numeric_level = level_map.get(logging_settings.level.upper(), logging.INFO)

        # Designation handlers
        handlers: list[logging.Handler] = []

        # Stdout handler
        if logging_settings.destination in ("stdout", "both"):
            stdout_handler = logging.StreamHandler(sys.stderr)
            stdout_handler.setLevel(numeric_level)
            handlers.append(stdout_handler)

        # File handler with timed rotation
        if logging_settings.destination in ("file", "both"):
            base_log_path: Path = logging_settings.file_path

            # Make relative to data_dir if not absolute
            if not base_log_path.is_absolute():
                base_log_path = shared_settings.data_dir / base_log_path

            base_log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = TimedRotatingFileHandler(
                filename=str(base_log_path),
                when=logging_settings.rotation_when,
                interval=1,
                backupCount=logging_settings.backup_count,
                encoding="utf-8",
                utc=False,  # local time for human-readable filenames
                delay=True,
            )
            file_handler.setLevel(numeric_level)
            handlers.append(file_handler)

        # Apply dynamic level early
        logging.basicConfig(
            level=numeric_level,
            format="%(message)s",  # structlog takes over formatting
            handlers=handlers
            or [logging.NullHandler()],  # avoid warnings if no handlers are configured
            force=True,
        )

        shared_processors = [
            structlog.stdlib.filter_by_level,  # respects logging level
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),  # ← fixed: handles %s / .format() args
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        # Renderer: pretty in dev/tty, JSON otherwise
        is_dev_like = sys.stderr.isatty() and shared_settings.app_env in (
            "development",
            "staging",
        )

        if is_dev_like:
            processors = shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True, sort_keys=True),
            ]
        else:
            processors = shared_processors + [
                structlog.processors.JSONRenderer(sort_keys=True),
            ]

        # Configure structlog with stdlib integration
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        cls._configured = True

    @classmethod
    def get_logger(
        cls,
        component: str | None = None,
        **initial_context: Any,
    ) -> structlog.stdlib.BoundLogger:
        """Get a configured, bound structured logger.

        Automatically validates context and adds edge=True when on Pi.

        Args:
            component: Module/service name (recommended)
            **initial_context: Extra fields to bind immediately

        Returns:
            Bound logger instance
        """
        cls.configure()

        ctx = LogContext(component=component, **initial_context)
        bound_fields = ctx.model_dump(exclude_none=True)

        # Auto-enrich with edge detection
        if shared_settings.is_edge_device:
            bound_fields.setdefault("edge", True)

        logger: structlog.stdlib.BoundLogger = structlog.get_logger()
        if bound_fields:
            logger = logger.bind(**bound_fields)

        return logger


# Public API
get_logger = StructuredLogging.get_logger
