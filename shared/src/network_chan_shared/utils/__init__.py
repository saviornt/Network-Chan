# shared/src/utils/__init__.py
"""Shared utilities submodule.

Contains logging, MQTT helpers, Pydantic models, etc. that are used
across appliance, assistant, and tests.
"""

from .logging_factory import get_logger, StructuredLogging

__all__ = ["get_logger", "StructuredLogging"]
