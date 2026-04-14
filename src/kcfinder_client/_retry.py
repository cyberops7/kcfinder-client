"""Retry decorators for transient HTTP failures."""

from __future__ import annotations

import asyncio
import functools
import time
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable

TRANSIENT_EXC = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
)


def _is_transient_response(r: httpx.Response) -> bool:
    return 500 <= r.status_code < 600


def _backoff_seconds(attempt: int) -> float:
    return 0.5 * (2**attempt)


def with_retry(method: Callable) -> Callable:
    """Retry decorator for sync client methods.

    Reads ``self._retries`` from the instance to determine the maximum
    number of retry attempts. Retries on connection errors and 5xx
    responses with exponential backoff.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                resp = method(self, *args, **kwargs)
            except TRANSIENT_EXC as e:
                last_exc = e
            else:
                if not _is_transient_response(resp) or attempt == self._retries:
                    return resp
                last_exc = None
            if attempt < self._retries:
                time.sleep(_backoff_seconds(attempt))
        raise last_exc  # type: ignore[misc]

    return wrapper


def with_retry_async(method: Callable) -> Callable:
    """Retry decorator for async client methods.

    Async counterpart of :func:`with_retry`.
    """

    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        last_exc: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                resp = await method(self, *args, **kwargs)
            except TRANSIENT_EXC as e:
                last_exc = e
            else:
                if not _is_transient_response(resp) or attempt == self._retries:
                    return resp
                last_exc = None
            if attempt < self._retries:
                await asyncio.sleep(_backoff_seconds(attempt))
        raise last_exc  # type: ignore[misc]

    return wrapper
