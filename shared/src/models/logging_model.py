"""Pydantic model definitions for structured logging context in Network-Chan.

This module defines LogContext — the validated container for bound log fields.
It is used by the logging factory and can be imported/extended by other modules.

Fields here are the "standard" structured keys available in every log message.
Extra fields are allowed (extra="allow") for flexibility.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogContext(BaseModel):
    """Pydantic-validated context container for structured log entries.

    All standard fields are optional except where explicitly required.
    Extra fields are permitted and passed through to structlog.bind().

    This model is frozen=False so fields can be mutated post-creation if needed
    (though this is rare in practice).

    Standard fields:
        component: Primary logger identity (e.g. "governance_settings", "telemetry_ingest")
        autonomy_mode: Current autonomy level name (normalized to UPPER)
        device_id: Hardware/device identifier (e.g. "pi-appliance-01", "ap-05")
        incident_id: Unique ID of the active incident being logged
        edge: Automatically set to True on Raspberry Pi/Appliance
        request_id: Correlation ID for tracing requests across services

    Usage:
        from shared.src.models.logging_model import LogContext

        ctx = LogContext(component="governance_settings", incident_id="inc-123")
        bound = ctx.model_dump(exclude_none=True)
    """

    model_config = ConfigDict(extra="allow", frozen=False)

    component: str | None = Field(
        default=None,
        description="Primary module/service/component name for this logger",
    )
    autonomy_mode: str | None = Field(
        default=None,
        description="Current autonomy level (normalized to uppercase string)",
    )
    device_id: str | None = Field(
        default=None,
        description="Identifier of the device/appliance generating the log",
    )
    incident_id: str | None = Field(
        default=None,
        description="Unique identifier of the active incident (if applicable)",
    )
    edge: bool = Field(
        default=False,
        description="True if running on edge/Appliance hardware (Raspberry Pi)",
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation/tracing ID for cross-service requests",
    )

    @field_validator("autonomy_mode", mode="before")
    @classmethod
    def normalize_autonomy(cls, v: Any) -> str | None:
        """Normalize autonomy_mode to uppercase string or None.

        Ensures consistent casing in logs regardless of source format.
        """
        return str(v).upper() if v is not None else None

    # Future extension point: add more standard fields here (e.g. user_id, trace_id)


__all__ = ["LogContext"]
