"""Thread-safe bridge for calling async functions from synchronous contexts.

When LLM-generated code calls `call_tool(...)` inside `exec()`, we are in a
synchronous frame that is *nested inside* an already-running asyncio event loop.
Calling ``asyncio.run()`` in that situation raises ``RuntimeError`` or deadlocks.

This module provides a dedicated background thread running its own event loop.
Coroutines are submitted via ``run_coroutine_threadsafe`` and the caller blocks
on the resulting ``Future`` — safe from any thread, synchronous or otherwise.
"""

import asyncio
import threading
from typing import Any, Coroutine


class AsyncBridge:
    """Run coroutines from synchronous code without deadlocking the main loop."""

    def __init__(self, timeout: float = 300.0):
        self._timeout = timeout
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True,
            name="async-bridge-worker",
        )
        self._thread.start()

    def run_async(self, coro: Coroutine) -> Any:
        """Submit *coro* to the bridge loop and block until it completes.

        Parameters
        ----------
        coro : Coroutine
            An awaitable coroutine to execute.

        Returns
        -------
        Any
            The coroutine's return value.

        Raises
        ------
        Exception
            Re-raises any exception the coroutine raised.
        TimeoutError
            If the coroutine does not complete within ``self._timeout`` seconds.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=self._timeout)

    def shutdown(self):
        """Stop the background loop and join the thread.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._loop.is_closed():
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        if not self._loop.is_closed():
            self._loop.close()


# Module-level singleton so every agent shares a single bridge thread.
_bridge: AsyncBridge | None = None
_lock = threading.Lock()


def get_async_bridge(timeout: float = 300.0) -> AsyncBridge:
    """Return (and lazily create) the module-level AsyncBridge singleton."""
    global _bridge
    if _bridge is None:
        with _lock:
            if _bridge is None:
                _bridge = AsyncBridge(timeout=timeout)
    return _bridge
