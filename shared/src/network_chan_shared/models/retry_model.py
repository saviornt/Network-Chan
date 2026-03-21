"""Pydantic model for validated runtime retry configuration parameters.

This model holds retry parameters (derived from retry_settings) and provides
helper methods to generate tenacity-compatible strategies (stop, wait, retry).

Intended usage:
    config = RetryConfigModel(...)  # or loaded from settings
    retryer = tenacity.AsyncRetrying(
        stop=config.get_stop_strategy(),
        wait=config.get_wait_strategy(),
        retry=config.get_retry_predicate(),
        ...
    )
"""

from __future__ import annotations

import asyncio
from typing import Any, Tuple, Type

from pydantic import BaseModel, ConfigDict, Field

# TODO: Check this against utils/retry.py
from ..settings.retry_settings import retry_settings
from tenacity import (
    wait_random_exponential,
    wait_random,
    stop_after_attempt,
    retry_if_exception_type,
)


class RetryConfigModel(BaseModel):
    """
    Validated runtime configuration for retry behavior on transient failures.

    Attributes:
        max_attempts: Maximum number of retry attempts before exhaustion.
        min_wait_sec: Minimum wait time between attempts (seconds).
        max_wait_sec: Maximum wait time — exponential backoff caps here (seconds).
        jitter_sec: Maximum random jitter added per wait interval (seconds).
        retry_exceptions: Tuple of exception types considered transient and retryable.
            Permanent errors (e.g. ValueError, auth failures) bypass retry.

    All fields are validated at model construction via Pydantic v2.
    """

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown fields
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        frozen=True,  # Immutable config after creation
    )

    max_attempts: int = Field(
        default=retry_settings.max_attempts,
        ge=1,
        description="Maximum retry attempts before giving up",
    )
    min_wait_sec: float = Field(
        default=retry_settings.min_wait_sec,
        ge=0.0,
        description="Minimum wait time between attempts (seconds)",
    )
    max_wait_sec: float = Field(
        default=retry_settings.max_wait_sec,
        ge=0.0,
        description="Maximum wait time — exponential backoff caps here (seconds)",
    )
    jitter_sec: float = Field(
        default=retry_settings.jitter_sec,
        ge=0.0,
        description="Maximum random jitter added to each wait interval (seconds)",
    )
    retry_exceptions: Tuple[Type[Exception], ...] = Field(
        default_factory=lambda: (
            TimeoutError,
            ConnectionError,
            OSError,
            asyncio.TimeoutError,
        ),
        description=(
            "Exception types considered transient and retryable. "
            "Permanent errors bypass retry logic."
        ),
    )

    def get_wait_strategy(self) -> Any:
        """
        Returns a tenacity-compatible wait strategy: exponential backoff + uniform jitter.

        Returns:
            tenacity.wait_base: Composed wait function ready for AsyncRetrying.
        """
        return wait_random_exponential(
            multiplier=1.0, min=self.min_wait_sec, max=self.max_wait_sec
        ) + wait_random(0, self.jitter_sec)

    def get_stop_strategy(self) -> Any:
        """
        Returns a tenacity-compatible stop strategy based on max attempts.

        Returns:
            tenacity.stop_base: Stop function ready for AsyncRetrying.
        """
        return stop_after_attempt(self.max_attempts)

    def get_retry_predicate(self) -> Any:
        """
        Returns a tenacity-compatible retry predicate for configured exceptions.

        Returns:
            tenacity.retry_base: Retry predicate function ready for AsyncRetrying.
        """
        return retry_if_exception_type(self.retry_exceptions)


__all__ = ["RetryConfigModel"]
