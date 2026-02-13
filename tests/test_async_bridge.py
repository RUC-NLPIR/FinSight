"""Tests for src.utils.async_bridge — the sync→async bridge.

These tests prove:
1. A coroutine can be run from a synchronous context via the bridge.
2. A coroutine can be run from *inside* an already-running asyncio loop
   (the exact scenario that caused the asyncio.run() deadlock).
3. Exceptions propagate correctly.
4. Timeout enforcement works.
5. The singleton accessor always returns the same instance.
"""

import asyncio
import threading
import time

import pytest

from src.utils.async_bridge import AsyncBridge, get_async_bridge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _add(a: int, b: int) -> int:
    """Simple async addition for testing."""
    await asyncio.sleep(0.01)
    return a + b


async def _fail():
    """Coroutine that always raises."""
    raise ValueError("intentional failure")


async def _slow(seconds: float):
    """Coroutine that sleeps — used for timeout tests."""
    await asyncio.sleep(seconds)
    return "done"


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestAsyncBridge:
    """Tests for the AsyncBridge class."""

    def test_run_async_from_sync(self):
        """Basic: call an async func from sync code via bridge."""
        bridge = AsyncBridge(timeout=10)
        try:
            result = bridge.run_async(_add(3, 4))
            assert result == 7
        finally:
            bridge.shutdown()

    def test_run_async_from_inside_event_loop(self):
        """Critical: call bridge.run_async while an asyncio loop is running.

        This reproduces the original deadlock scenario.
        """
        bridge = AsyncBridge(timeout=10)
        try:
            async def _inner():
                # We are inside a running loop — asyncio.run() would deadlock.
                result = bridge.run_async(_add(10, 20))
                return result

            result = asyncio.run(_inner())
            assert result == 30
        finally:
            bridge.shutdown()

    def test_exception_propagation(self):
        """Exceptions raised inside the coroutine propagate to the caller."""
        bridge = AsyncBridge(timeout=10)
        try:
            with pytest.raises(ValueError, match="intentional failure"):
                bridge.run_async(_fail())
        finally:
            bridge.shutdown()

    def test_timeout(self):
        """Bridge raises TimeoutError when the coroutine exceeds the limit."""
        bridge = AsyncBridge(timeout=0.2)
        try:
            with pytest.raises(TimeoutError):
                bridge.run_async(_slow(5.0))
        finally:
            bridge.shutdown()

    def test_multiple_concurrent_calls(self):
        """Multiple threads can submit coroutines concurrently."""
        bridge = AsyncBridge(timeout=10)
        results = [None] * 5
        errors = []

        def _worker(idx: int):
            try:
                results[idx] = bridge.run_async(_add(idx, idx))
            except Exception as exc:
                errors.append(exc)

        try:
            threads = [threading.Thread(target=_worker, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)
            assert not errors, f"Errors in threads: {errors}"
            assert results == [0, 2, 4, 6, 8]
        finally:
            bridge.shutdown()

    def test_shutdown_idempotent(self):
        """Calling shutdown() twice does not raise."""
        bridge = AsyncBridge(timeout=10)
        bridge.shutdown()
        bridge.shutdown()  # should not raise


class TestGetAsyncBridge:
    """Tests for the module-level singleton accessor."""

    def test_singleton(self):
        """get_async_bridge() always returns the same instance."""
        b1 = get_async_bridge()
        b2 = get_async_bridge()
        assert b1 is b2

    def test_singleton_works(self):
        """The singleton bridge can actually run coroutines."""
        bridge = get_async_bridge()
        assert bridge.run_async(_add(100, 200)) == 300
