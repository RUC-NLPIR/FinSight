"""Tests for src.utils.rate_limiter — async token-bucket rate limiter.

Proves:
1. Unconfigured services are not rate-limited.
2. Configured services enforce minimum intervals.
3. Per-service isolation (service A's limit doesn't affect service B).
4. set_interval works at runtime.
"""

import asyncio
import time

import pytest

from src.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_unconfigured_service_no_delay(self):
        """Services not in the config should return immediately."""
        limiter = RateLimiter({"other": 5.0})
        start = time.monotonic()
        await limiter.acquire("unknown_service")
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self):
        """Two rapid calls to the same service should be spaced by the interval."""
        limiter = RateLimiter({"api": 0.3})
        await limiter.acquire("api")
        start = time.monotonic()
        await limiter.acquire("api")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.25, f"Expected >=0.25s delay, got {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_per_service_isolation(self):
        """Rate-limiting service A should not delay service B."""
        limiter = RateLimiter({"slow": 1.0, "fast": 0.0})
        await limiter.acquire("slow")
        start = time.monotonic()
        await limiter.acquire("fast")  # fast has 0 interval
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_set_interval_runtime(self):
        """set_interval should update rate limits at runtime."""
        limiter = RateLimiter({})
        # Initially no limit
        start = time.monotonic()
        await limiter.acquire("svc")
        await limiter.acquire("svc")
        assert time.monotonic() - start < 0.1

        # Now set a limit
        limiter.set_interval("svc", 0.3)
        await limiter.acquire("svc")
        start = time.monotonic()
        await limiter.acquire("svc")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.25

    @pytest.mark.asyncio
    async def test_empty_config(self):
        """RateLimiter with no config should not block anything."""
        limiter = RateLimiter()
        start = time.monotonic()
        for _ in range(10):
            await limiter.acquire("anything")
        assert time.monotonic() - start < 0.1
