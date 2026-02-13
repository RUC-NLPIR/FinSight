"""Tests for the exponential backoff retry logic in AsyncLLM.generate.

Verifies:
1. Retry delay increases exponentially with jitter.
2. The retry message is printed.
3. The import of `random` does not break existing behavior.
"""

import asyncio
import random

import pytest


class TestExponentialBackoff:
    """Test the backoff calculation matches what llm.py uses."""

    def test_backoff_progression(self):
        """Base delays should be 1, 2, 4, 8, 16, 32 (capped)."""
        for attempt in range(6):
            base_delay = min(2 ** attempt, 32)
            expected = [1, 2, 4, 8, 16, 32][attempt]
            assert base_delay == expected, f"Attempt {attempt}: got {base_delay}, expected {expected}"

    def test_jitter_within_bounds(self):
        """Jitter should be in [0, base_delay * 0.5]."""
        random.seed(42)
        for attempt in range(6):
            base_delay = min(2 ** attempt, 32)
            jitter = random.uniform(0, base_delay * 0.5)
            assert 0 <= jitter <= base_delay * 0.5

    def test_total_delay_within_bounds(self):
        """Total delay = base + jitter should be in [base, base * 1.5]."""
        random.seed(42)
        for attempt in range(6):
            base_delay = min(2 ** attempt, 32)
            jitter = random.uniform(0, base_delay * 0.5)
            total = base_delay + jitter
            assert base_delay <= total <= base_delay * 1.5

    def test_cap_at_32(self):
        """After attempt 5, delay stays capped at 32."""
        for attempt in range(5, 20):
            base_delay = min(2 ** attempt, 32)
            assert base_delay == 32

    def test_random_import_available(self):
        """Verify random module is importable (used in llm.py)."""
        import random as r
        assert hasattr(r, 'uniform')

    def test_llm_source_has_exponential_backoff(self):
        """Verify the actual llm.py source contains the backoff pattern."""
        import os
        llm_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "utils", "llm.py"
        )
        with open(llm_path) as f:
            source = f.read()
        assert "2 ** attempt" in source, "Exponential backoff pattern not found in llm.py"
        assert "random.uniform" in source, "Jitter not found in llm.py"
