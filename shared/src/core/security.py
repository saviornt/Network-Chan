"""Security utilities shared across Network-Chan components.

This module provides lightweight, reusable helpers for:
- Data redaction (PII masking in logs/telemetry/embeddings)
- Basic RBAC/role checks (in-memory; extendable to policy engine)
- Action permission checks tied to autonomy mode and roles

All functions are pure or take explicit inputs — no global state.
Designed to be fast and safe for edge (Appliance) use.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal

import pyotp
from pydantic import BaseModel, Field

from src.config.shared_settings import AutonomyLevel, shared_settings


class UserContext(BaseModel):
    """Minimal context about the current actor (user/agent/LLM).

    Used for permission checks and audit logging.
    """

    username: str = Field(..., min_length=3)
    roles: List[Literal["admin", "operator", "viewer", "agent"]] = Field(
        default_factory=list
    )
    is_llm_generated: bool = Field(
        default=False, description="True if action comes from LLM suggestion"
    )


def redact_pii(value: Any, deep: bool = True) -> Any:
    """Redact personally identifiable information from a value for safe logging/embedding.

    Handles common patterns: IP addresses, MACs, emails, passwords, tokens.

    Args:
        value: Input to redact (str, dict, list, or primitive).
        deep: If True, recursively redact dicts/lists.

    Returns:
        Redacted representation (str, dict, or list).
    """
    if isinstance(value, str):
        # IP addresses (v4/v6 rough match)
        value = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_REDACTED]", value)
        value = re.sub(
            r"\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b", "[MAC_REDACTED]", value
        )
        # Emails
        value = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL_REDACTED]",
            value,
        )
        # Tokens / secrets (rough hex/base64-like)
        value = re.sub(r"\b[A-Za-z0-9+/=]{20,}\b", "[TOKEN_REDACTED]", value)
        return value

    if deep:
        if isinstance(value, dict):
            return {k: redact_pii(v, deep=True) for k, v in value.items()}
        if isinstance(value, list):
            return [redact_pii(item, deep=True) for item in value]

    return str(value)


def is_action_allowed(
    action_name: str,
    user: UserContext,
    current_autonomy: AutonomyLevel = shared_settings.autonomous_mode,
) -> bool:
    """Check if a given action is permitted under current autonomy mode and user roles.

    Rough initial rules — will be replaced/extended by full policy engine.

    Args:
        action_name: Descriptive name (e.g., "change_wifi_channel", "reboot_device").
        user: Current actor context.
        current_autonomy: Active autonomy level.

    Returns:
        True if allowed, False otherwise.
    """
    # High-risk actions always require admin + sufficient autonomy
    high_risk_actions = {
        "reboot_device",
        "factory_reset",
        "change_management_vlan",
        "execute_arbitrary_command",
    }

    if action_name in high_risk_actions:
        return "admin" in user.roles and current_autonomy >= AutonomyLevel.AUTONOMOUS

    # Medium-risk: operator or admin, supervised+
    medium_risk_actions = {
        "change_wifi_channel",
        "throttle_client",
        "block_mac",
        "update_firmware",
    }

    if action_name in medium_risk_actions:
        return (
            "admin" in user.roles or "operator" in user.roles
        ) and current_autonomy >= AutonomyLevel.SUPERVISED

    # Low-risk / read-only: almost always allowed
    return True


def mask_sensitive_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive fields in a settings-like dict before logging/export.

    Args:
        data: Dict (e.g. settings.model_dump())

    Returns:
        Copy with sensitive values replaced.
    """
    sensitive_keys = {
        "secret_key",
        "jwt_secret",
        "password_salt",
        "admin_password_hash",
        "admin_totp_secret",
        "mqtt_password",
    }

    result = data.copy()
    for key in sensitive_keys:
        if key in result:
            result[key] = "[REDACTED]"

    return result


# TODO: Remove the following TOTP helper since it is (or should be) fully handled by pyotp in auth_service.py. Kept here for now since some logic is shared between API and service layers, but may be refactored later.
def check_totp_code(
    secret: str | None,
    provided_code: str,
    *,
    window: int = 1,
) -> bool:
    """Validate a TOTP code against the stored secret using pyotp (or stub fallback).

    Args:
        secret: Base32-encoded TOTP secret from settings (None = 2FA disabled).
        provided_code: 6-digit code submitted by user.
        window: Allow codes from ±window time steps (default 1 = ±30 seconds).

    Returns:
        True if the code is valid, False otherwise.
    """
    if not secret:
        # No secret configured → 2FA is disabled → always pass
        return True

    if not provided_code or not provided_code.isdigit() or len(provided_code) != 6:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(provided_code, valid_window=window)
