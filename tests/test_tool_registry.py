"""Tests for the tool auto-registration system in src.tools.__init__.

Proves that:
1. US market tools are auto-discovered and registered.
2. Existing Chinese market tools remain registered.
3. get_tool_by_name returns the correct class.
4. list_tools includes the new US tools.
"""

import pytest


class TestToolRegistry:
    """Verify the auto-registration picks up all tools."""

    def test_us_tools_registered(self):
        from src.tools import list_tools
        tools = list_tools()
        us_expected = [
            "US Stock profile",
            "US Stock price history",
            "US Balance sheet",
            "US Income statement",
            "US Cash-flow statement",
            "US Shareholding structure",
        ]
        for name in us_expected:
            assert name in tools, f"US tool '{name}' not found in registry"

    def test_chinese_tools_still_registered(self):
        """Chinese tools are registered when akshare is available."""
        try:
            import akshare  # noqa: F401
        except ImportError:
            pytest.skip("akshare not installed — Chinese tools cannot be loaded")

        from src.tools import list_tools
        tools = list_tools()
        cn_expected = [
            "Stock profile",
            "Balance sheet",
            "Income statement",
            "Cash-flow statement",
        ]
        for name in cn_expected:
            assert name in tools, f"Chinese tool '{name}' not found in registry"

    def test_get_tool_by_name(self):
        from src.tools import get_tool_by_name
        from src.tools.financial.us_market import USStockProfile
        cls = get_tool_by_name("US Stock profile")
        assert cls is USStockProfile

    def test_categories_include_financial(self):
        from src.tools import get_tool_categories
        cats = get_tool_categories()
        assert "financial" in cats
        assert "US Stock profile" in cats["financial"]
