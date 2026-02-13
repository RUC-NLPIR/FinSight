"""Async-friendly per-service rate limiter using a token-bucket algorithm.

Usage::

    limiter = RateLimiter({"search_engines": 1.0, "yfinance": 0.2})
    await limiter.acquire("search_engines")  # blocks until a token is available
"""

import asyncio
import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Per-service token-bucket rate limiter.

    Parameters
    ----------
    service_intervals : dict[str, float]
        Mapping of service names to minimum seconds between calls.
        Example: ``{"search_engines": 1.0, "yfinance": 0.2}``
    """

    def __init__(self, service_intervals: Dict[str, float] | None = None):
        self._intervals: Dict[str, float] = service_intervals or {}
        self._last_call: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, service: str) -> asyncio.Lock:
        if service not in self._locks:
            self._locks[service] = asyncio.Lock()
        return self._locks[service]

    async def acquire(self, service: str) -> None:
        """Wait until the rate limit for *service* allows a call.

        If *service* is not configured, returns immediately (no limit).
        """
        interval = self._intervals.get(service)
        if interval is None or interval <= 0:
            return

        lock = self._get_lock(service)
        async with lock:
            now = time.monotonic()
            last = self._last_call.get(service, 0.0)
            wait = interval - (now - last)
            if wait > 0:
                logger.debug(
                    "Rate limiter: delaying %s call by %.2fs (interval=%.2fs)",
                    service, wait, interval,
                )
                await asyncio.sleep(wait)
            self._last_call[service] = time.monotonic()

    def set_interval(self, service: str, seconds: float) -> None:
        """Update or add a rate limit for *service* at runtime."""
        self._intervals[service] = seconds
