"""Bounded retry helpers shared by external API and read-only DB calls."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")
MAX_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 0.05
MAX_BACKOFF_SECONDS = 0.2
DEFAULT_TIMEOUT_SECONDS = 3.0


def _backoff_seconds(failed_attempt: int, base: float, maximum: float) -> float:
    return min(base * (2**failed_attempt), maximum)


def retry_sync(
    operation: Callable[[], T],
    *,
    max_attempts: int = MAX_ATTEMPTS,
    base_backoff_seconds: float = BASE_BACKOFF_SECONDS,
    max_backoff_seconds: float = MAX_BACKOFF_SECONDS,
    should_retry: Callable[[Exception], bool] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run an idempotent operation with a bounded exponential-backoff retry."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    retryable = should_retry or (lambda _error: True)
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as error:
            if attempt + 1 >= max_attempts or not retryable(error):
                raise
            sleep(_backoff_seconds(attempt, base_backoff_seconds, max_backoff_seconds))
    raise RuntimeError("retry loop exhausted unexpectedly")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_attempts: int = MAX_ATTEMPTS,
    base_backoff_seconds: float = BASE_BACKOFF_SECONDS,
    max_backoff_seconds: float = MAX_BACKOFF_SECONDS,
    should_retry: Callable[[Exception], bool] | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Run an async operation with a per-attempt timeout and bounded retry."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    retryable = should_retry or (lambda _error: True)
    for attempt in range(max_attempts):
        try:
            return await asyncio.wait_for(operation(), timeout=timeout_seconds)
        except Exception as error:
            if attempt + 1 >= max_attempts or not retryable(error):
                raise
            await sleep(_backoff_seconds(attempt, base_backoff_seconds, max_backoff_seconds))
    raise RuntimeError("retry loop exhausted unexpectedly")
