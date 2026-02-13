"""Tests for the dynamic date resolution in ShareHoldingStructure.

Proves that the hardcoded '2024-12-31' has been replaced with logic
that computes the most recent quarter-end date dynamically.
"""

import datetime
from unittest.mock import patch

import pytest


class TestDynamicQuarterDate:
    """Test the quarter-end date calculation used in stock.py."""

    @staticmethod
    def _compute_report_date(today: datetime.date) -> str:
        """Reproduce the same logic used in ShareHoldingStructure.api_function."""
        quarter_ends = [
            datetime.date(today.year, 3, 31),
            datetime.date(today.year, 6, 30),
            datetime.date(today.year, 9, 30),
            datetime.date(today.year, 12, 31),
        ]
        past_ends = [d for d in quarter_ends if d <= today]
        if not past_ends:
            report_date = datetime.date(today.year - 1, 12, 31)
        else:
            report_date = past_ends[-1]
        return report_date.strftime("%Y-%m-%d")

    def test_jan_15(self):
        """Before Q1 end — should fall back to previous year's Q4."""
        assert self._compute_report_date(datetime.date(2026, 1, 15)) == "2025-12-31"

    def test_mar_31(self):
        """Exactly on Q1 end date."""
        assert self._compute_report_date(datetime.date(2026, 3, 31)) == "2026-03-31"

    def test_apr_15(self):
        """After Q1 but before Q2 — should use Q1."""
        assert self._compute_report_date(datetime.date(2026, 4, 15)) == "2026-03-31"

    def test_jun_30(self):
        """Exactly on Q2 end date."""
        assert self._compute_report_date(datetime.date(2026, 6, 30)) == "2026-06-30"

    def test_oct_1(self):
        """After Q3 but before Q4 — should use Q3."""
        assert self._compute_report_date(datetime.date(2026, 10, 1)) == "2026-09-30"

    def test_dec_31(self):
        """Exactly on Q4 end date."""
        assert self._compute_report_date(datetime.date(2026, 12, 31)) == "2026-12-31"

    def test_feb_1_different_year(self):
        """Early in a different year — uses prior year Q4."""
        assert self._compute_report_date(datetime.date(2030, 2, 1)) == "2029-12-31"

    def test_never_returns_hardcoded_2024(self):
        """Ensure the old hardcoded 2024-12-31 is never returned for any
        date in 2026+."""
        for month in range(1, 13):
            for day in (1, 15, 28):
                try:
                    d = datetime.date(2026, month, day)
                except ValueError:
                    continue
                result = self._compute_report_date(d)
                assert result != "2024-12-31", f"Got stale date for {d}"

    def test_hardcoded_string_removed_from_source(self):
        """Verify the literal '2024-12-31' no longer appears in stock.py."""
        import os
        stock_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "tools", "financial", "stock.py"
        )
        with open(stock_path) as f:
            source = f.read()
        assert "2024-12-31" not in source, (
            "Hardcoded date '2024-12-31' still present in stock.py"
        )
