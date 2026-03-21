"""Retry utilities for resilient handling of transient failures in Network-Chan.

This module provides decorators to automatically retry operations that may fail
due to temporary issues (timeouts, connection resets, etc.).

Features:
- Exponential backoff + jitter to avoid thundering herd.
- Structured logging on each retry attempt.
- Configurable via modular retry_settings (max attempts, waits, jitter).
- Async and sync variants.
- Raises NetworkExhaustedError when all retries fail.

Usage examples:
    @aretry_network
    async def mqtt_publish(...):
        ...

    @retry_network
    def netmiko_execute(...):
        ...
"""

import asyncio
import functools
from typing import Awaitable, Callable, ParamSpec, TypeVar

import tenacity
from tenacity import RetryCallState, retry_if_exception_type, stop_after_attempt

from shared.settings.retry_settings import retry_settings
from shared.utils.logging_factory import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class NetworkRetryError(Exception):
    """Base class for retry-related errors in Network-Chan."""


class NetworkExhaustedError(NetworkRetryError, tenacity.RetryError):
    """
    All configured retry attempts have been exhausted.

    Attributes:
        last_exception: The final exception that caused failure (if any).
    """

    last_attempt: tenacity.RetryCallState
    last_exception: Exception | None = None

    def __init__(self, last_attempt: tenacity.RetryCallState) -> None:
        self.last_attempt = last_attempt

        if last_attempt.outcome is not None and last_attempt.outcome.failed:
            exc = last_attempt.outcome.exception()
            if isinstance(exc, Exception):
                self.last_exception = exc

    def __str__(self) -> str:
        attempts = self.last_attempt.attempt_number
        if self.last_exception:
            return f"Retry exhausted after {attempts} attempts. Last error: {self.last_exception!r}"
        return f"Retry exhausted after {attempts} attempts."


def _log_before_retry(retry_state: RetryCallState) -> None:
    """
    Structured log hook called before each sleep/retry attempt.

    Logs attempt number, next delay, and exception (if failed).
    """
    if retry_state.outcome is None or not retry_state.outcome.failed:
        return

    exc = retry_state.outcome.exception()
    logger.warning(
        "Retrying failed operation",
        attempt_number=retry_state.attempt_number,
        next_delay_sec=round(retry_state.next_action.sleep, 2)
        if retry_state.next_action
        else 0.0,
        exception=repr(exc) if exc else None,
        function_name=retry_state.fn.__name__ if retry_state.fn else "unknown",
    )


def aretry_network(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """
    Async decorator: retry transient failures with exponential backoff + jitter.

    Retries only on configured exceptions from retry_settings.
    Logs each attempt via structured logger.
    Raises NetworkExhaustedError on final failure.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        retryer = tenacity.AsyncRetrying(
            stop=stop_after_attempt(retry_settings.max_attempts),
            wait=tenacity.wait_random_exponential(
                multiplier=1.0,
                min=retry_settings.min_wait_sec,
                max=retry_settings.max_wait_sec,
            )
            + tenacity.wait_random(max=retry_settings.jitter_sec),
            retry=retry_if_exception_type(
                (
                    TimeoutError,
                    ConnectionError,
                    OSError,
                    asyncio.TimeoutError,
                    # Extend later: MQTTException, paramiko.SSHException, etc.
                )
            ),
            before_sleep=_log_before_retry,
            reraise=True,  # Preserve original traceback on final raise
        )

        try:
            return await retryer(func, *args, **kwargs)
        except tenacity.RetryError as exc:
            raise NetworkExhaustedError(exc.last_attempt) from exc  # type: ignore[attr-defined]

    return wrapper


def retry_network(func: Callable[P, R]) -> Callable[P, R]:
    """
    Synchronous decorator: same retry logic for blocking calls (e.g. Netmiko).

    Retries on configured exceptions, logs attempts, raises NetworkExhaustedError
    when exhausted.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        retryer = tenacity.Retrying(
            stop=stop_after_attempt(retry_settings.max_attempts),
            wait=tenacity.wait_random_exponential(
                multiplier=1.0,
                min=retry_settings.min_wait_sec,
                max=retry_settings.max_wait_sec,
            )
            + tenacity.wait_random(max=retry_settings.jitter_sec),
            retry=retry_if_exception_type(
                (TimeoutError, ConnectionError, OSError)  # Extend as needed
            ),
            before_sleep=_log_before_retry,
            reraise=True,
        )

        try:
            return retryer(func, *args, **kwargs)
        except tenacity.RetryError as exc:
            raise NetworkExhaustedError(exc.last_attempt) from exc  # type: ignore[attr-defined]

    return wrapper
