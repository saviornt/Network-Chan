"""Custom exceptions for the Network-Chan project.

This module defines domain-specific exceptions used across shared code,
Appliance (edge), and Assistant (central). All exceptions inherit from
built-in Exception or more specific bases to allow proper catching.

Guidelines followed:
- Use descriptive names that explain "what went wrong".
- Provide context via attributes (e.g., error_code, details dict).
- Prefer specific exceptions over generic ones where possible.
"""

from typing import Any, Dict


class NetworkChanError(Exception):
    """Base exception for all Network-Chan specific errors.

    All custom exceptions in the project should inherit from this class
    to allow broad catching when needed (e.g., in global error handlers).
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: Dict[str, Any] | None = None,
    ) -> None:
        """Initialize the base Network-Chan exception.

        Args:
            message: Human-readable error description.
            error_code: Optional short code (e.g., "POL-001", "RL-INV-STATE").
            details: Optional dict with extra context (device_ip, model_name, etc.).
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """String representation with code and details if present."""
        parts = [self.message]
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " ".join(parts)


# =============================================================================
# Configuration & Settings Errors
# =============================================================================
class ConfigurationError(NetworkChanError):
    """Raised when settings validation or loading fails."""

    pass


class InvalidAutonomyModeError(ConfigurationError):
    """Raised when an invalid or unsafe autonomy level transition is attempted."""

    pass


# =============================================================================
# Validation & Data Errors
# =============================================================================
class ValidationError(NetworkChanError):
    """Base for data/model validation failures (Pydantic-level or custom)."""

    pass


class InvalidTelemetryDataError(ValidationError):
    """Telemetry features are malformed, missing required fields, or out of range."""

    pass


class InvalidRLStateError(ValidationError):
    """RL state vector has incorrect shape, NaN values, or invalid bounds."""

    pass


# =============================================================================
# Policy & Governance Errors
# =============================================================================
class PolicyViolationError(NetworkChanError):
    """Action was blocked by current autonomy mode, RBAC, or safety policy."""

    def __init__(
        self,
        message: str,
        action: str,
        current_mode: int,
        required_mode: int,
        **details: Any,
    ) -> None:
        """Initialize with action and mode context.

        Args:
            message: Base error message.
            action: The attempted action (e.g., "change_channel", "reboot_port").
            current_mode: Current autonomy level (0–5).
            required_mode: Minimum level needed for this action.
            **details: Additional context.
        """
        details = details or {}
        details.update(
            {
                "action": action,
                "current_mode": current_mode,
                "required_mode": required_mode,
            }
        )
        super().__init__(
            message=message
            or f"Action '{action}' not allowed in mode {current_mode} (needs >= {required_mode})",
            error_code="POL-VIOL",
            details=details,
        )


# =============================================================================
# Integration & External Service Errors
# =============================================================================
class IntegrationError(NetworkChanError):
    """Base for failures in external integrations (MQTT, Omada, Netmiko, etc.)."""

    pass


class MQTTConnectionError(IntegrationError):
    """Failed to connect, publish, or subscribe to MQTT broker."""

    pass


class DeviceCommunicationError(IntegrationError):
    """Failed to query or command a network device (Omada API, SNMP, Netmiko)."""

    pass


# =============================================================================
# ML / RL Specific Errors
# =============================================================================
class MLModelError(NetworkChanError):
    """Base for model loading, inference, or training failures."""

    pass


class RLConvergenceError(MLModelError):
    """Reinforcement learning process failed to converge or produced NaN rewards."""

    pass


class InvalidActionProposalError(MLModelError):
    """Proposed action from RL/LLM is invalid or unsafe for current state."""

    pass


# =============================================================================
# Recovery & Operational Errors
# =============================================================================
class RollbackFailedError(NetworkChanError):
    """Automatic or manual rollback of a configuration change failed."""

    pass


class RecoveryError(NetworkChanError):
    """General failure during system recovery (e.g., after crash or disconnect)."""

    pass
