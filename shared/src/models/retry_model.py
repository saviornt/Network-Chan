"""Pydantic model for validated runtime retry configuration parameters.

This module defines RetryConfig, a runtime-validated Pydantic BaseModel that
holds retry parameters (typically derived from SharedSettings). It provides
helper methods to generate tenacity-compatible strategies.

Intended usage:
    config = RetryConfig(...)  # or loaded from settings
    retryer = tenacity.AsyncRetrying(
        stop=config.get_stop_strategy(),
        wait=config.get_wait_strategy(),
        retry=config.get_retry_predicate(),
        ...
    )
"""

import asyncio
from typing import Any, Tuple, Type

from pydantic import BaseModel, Field
from shared.src.config.retry_settings import retry_settings


class RetryConfig(BaseModel):
    """
    Validated runtime configuration for retry behavior on transient failures.

    Attributes:
        max_attempts: Maximum number of retry attempts before exhaustion.
        min_wait_sec: Minimum wait time between attempts (seconds).
        max_wait_sec: Maximum wait time — exponential backoff caps here (seconds).
        jitter_sec: Maximum random jitter added per wait interval (seconds).
        retry_exceptions: Tuple of exception types considered transient and
            retryable. Permanent errors (e.g. ValueError, auth failures) bypass retry.

    All fields are validated at model construction via Pydantic v2.
    """

    max_attempts: int = retry_settings.max_attempts
    min_wait_sec: float = retry_settings.min_wait_sec
    max_wait_sec: float = retry_settings.max_wait_sec
    jitter_sec: float = retry_settings.jitter_sec
    retry_exceptions: Tuple[Type[Exception], ...] = Field(
        default_factory=lambda: (
            TimeoutError,
            ConnectionError,
            OSError,
            asyncio.TimeoutError,
        )
    )

    def get_wait_strategy(self) -> Any:
        """
        Returns a tenacity-compatible wait strategy: exponential backoff + uniform jitter.

        Returns:
            Any: Composed wait function ready for tenacity.Retrying (tenacity.wait_base internally).
        """
        from tenacity import wait_random_exponential, wait_random

        return wait_random_exponential(
            multiplier=1.0,
            min=self.min_wait_sec,
            max=self.max_wait_sec,
        ) + wait_random(0, self.jitter_sec)

    def get_stop_strategy(self) -> Any:
        """
        Returns a tenacity-compatible stop strategy based on max attempts.

        Returns:
            Any: Stop function ready for tenacity.Retrying (tenacity.stop_base internally).
        """
        from tenacity import stop_after_attempt

        return stop_after_attempt(self.max_attempts)

    def get_retry_predicate(self) -> Any:
        """
        Returns a tenacity-compatible retry predicate for configured exceptions.

        Returns:
            Any: Retry predicate function ready for tenacity.Retrying (tenacity.retry_base internally).
        """
        from tenacity import retry_if_exception_type

        return retry_if_exception_type(self.retry_exceptions)
