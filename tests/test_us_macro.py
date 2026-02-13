"""Tests for src.tools.macro.us_macro — US macroeconomic tools.

These tests verify:
1. Tool metadata (name, parameters) is correct.
2. FRED tools gracefully return ToolResult(data=None) when FRED_API_KEY is missing.
3. USMarketIndex works against live Yahoo Finance API.
"""

import os

import pandas as pd
import pytest

from src.tools.macro.us_macro import (
    USCPI,
    USGDP,
    USInterestRates,
    USMarketIndex,
    USUnemployment,
)
from src.tools.base import ToolResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cpi():
    return USCPI()


@pytest.fixture
def gdp():
    return USGDP()


@pytest.fixture
def unemployment():
    return USUnemployment()


@pytest.fixture
def interest():
    return USInterestRates()


@pytest.fixture
def market_index():
    return USMarketIndex()


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

class TestUSMacroMetadata:
    def test_cpi_name(self, cpi):
        assert cpi.name == "US CPI (FRED)"

    def test_gdp_name(self, gdp):
        assert gdp.name == "US GDP (FRED)"

    def test_unemployment_name(self, unemployment):
        assert unemployment.name == "US Unemployment rate (FRED)"

    def test_interest_name(self, interest):
        assert interest.name == "US Interest rates (FRED)"

    def test_market_index_name(self, market_index):
        assert market_index.name == "US Market index"


# ---------------------------------------------------------------------------
# FRED tools (graceful degradation without API key)
# ---------------------------------------------------------------------------

class TestFREDWithoutKey:
    """When FRED_API_KEY is not set, all FRED tools should return data=None."""

    @pytest.fixture(autouse=True)
    def _unset_fred_key(self, monkeypatch):
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        # Reset the cached _fred client
        import src.tools.macro.us_macro as mod
        mod._fred = None

    @pytest.mark.asyncio
    async def test_cpi_no_key(self, cpi):
        results = await cpi.api_function()
        assert len(results) == 1
        assert isinstance(results[0], ToolResult)
        assert results[0].data is None

    @pytest.mark.asyncio
    async def test_gdp_no_key(self, gdp):
        results = await gdp.api_function()
        assert results[0].data is None

    @pytest.mark.asyncio
    async def test_unemployment_no_key(self, unemployment):
        results = await unemployment.api_function()
        assert results[0].data is None

    @pytest.mark.asyncio
    async def test_interest_no_key(self, interest):
        results = await interest.api_function()
        assert results[0].data is None


# ---------------------------------------------------------------------------
# Market index (live Yahoo Finance)
# ---------------------------------------------------------------------------

class TestUSMarketIndex:
    @pytest.mark.asyncio
    async def test_sp500(self, market_index):
        results = await market_index.api_function(index_symbol="^GSPC", period="5d")
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty
        assert "Close" in r.data.columns
        assert "S&P 500" in r.name

    @pytest.mark.asyncio
    async def test_nasdaq(self, market_index):
        results = await market_index.api_function(index_symbol="^IXIC", period="5d")
        r = results[0]
        assert isinstance(r.data, pd.DataFrame)
        assert "NASDAQ" in r.name
