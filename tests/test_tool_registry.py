"""Tests for tool auto-registration and merged US market support."""

import pytest


class TestToolRegistry:
    """Verify the auto-registration picks up all tools."""

    def test_core_financial_tools_registered(self):
        from src.tools import list_tools
        tools = list_tools()
        expected = [
            "Stock profile",
            "Stock candlestick data",
            "Balance sheet",
            "Income statement",
            "Cash-flow statement",
            "Shareholding structure",
        ]
        for name in expected:
            assert name in tools, f"Financial tool '{name}' not found in registry"

    def test_no_dedicated_us_tool_classes(self):
        from src.tools import list_tools
        tools = list_tools()
        unexpected = [
            "US Stock profile",
            "US Stock price history",
            "US Balance sheet",
            "US Income statement",
            "US Cash-flow statement",
            "US Shareholding structure",
        ]
        for name in unexpected:
            assert name not in tools, f"Unexpected dedicated US tool '{name}' still registered"

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
        from src.tools.financial.stock import StockBasicInfo
        cls = get_tool_by_name("Stock profile")
        assert cls is StockBasicInfo

    def test_categories_include_financial(self):
        from src.tools import get_tool_categories
        cats = get_tool_categories()
        assert "financial" in cats
        assert "Stock profile" in cats["financial"]
