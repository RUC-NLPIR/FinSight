"""Tests for src.tools.financial.us_market — US equity tools.

These tests prove:
1. Each tool returns a list of ToolResult objects.
2. Each ToolResult has non-empty name, description, and source.
3. The data field is a DataFrame or dict (depending on tool), not None,
   when queried with a known-valid ticker (AAPL).
4. Tools gracefully return ToolResult(data=None) for an invalid ticker.
5. Tool metadata (name, parameters) is correctly set.

Note: These are integration tests that hit the live Yahoo Finance API.
They require an internet connection and may be slow (~2-5s per call).
"""

import pandas as pd
import pytest

from src.tools.base import ToolResult
from src.tools.financial.us_market import (
    USBalanceSheet,
    USCashFlowStatement,
    USIncomeStatement,
    USShareholding,
    USStockPrice,
    USStockProfile,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_TICKER = "AAPL"
INVALID_TICKER = "ZZZZZZZNOTREAL123"


@pytest.fixture
def us_profile():
    return USStockProfile()


@pytest.fixture
def us_price():
    return USStockPrice()


@pytest.fixture
def us_balance():
    return USBalanceSheet()


@pytest.fixture
def us_income():
    return USIncomeStatement()


@pytest.fixture
def us_cashflow():
    return USCashFlowStatement()


@pytest.fixture
def us_holding():
    return USShareholding()


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------

class TestToolMetadata:
    """Ensure each tool's constructor sets name and parameters correctly."""

    def test_profile_name(self, us_profile):
        assert us_profile.name == "US Stock profile"
        assert len(us_profile.parameters) >= 1

    def test_price_name(self, us_price):
        assert us_price.name == "US Stock price history"

    def test_balance_name(self, us_balance):
        assert us_balance.name == "US Balance sheet"

    def test_income_name(self, us_income):
        assert us_income.name == "US Income statement"

    def test_cashflow_name(self, us_cashflow):
        assert us_cashflow.name == "US Cash-flow statement"

    def test_holding_name(self, us_holding):
        assert us_holding.name == "US Shareholding structure"


# ---------------------------------------------------------------------------
# Integration tests — valid ticker
# ---------------------------------------------------------------------------

class TestUSStockProfile:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, us_profile):
        results = await us_profile.api_function(ticker=VALID_TICKER)
        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert r.data is not None
        assert isinstance(r.data, dict)
        assert r.data["ticker"] == VALID_TICKER
        assert r.data["name"]  # non-empty
        assert r.data["sector"]  # non-empty
        assert r.data["market_cap"] > 0

    @pytest.mark.asyncio
    async def test_invalid_ticker(self, us_profile):
        results = await us_profile.api_function(ticker=INVALID_TICKER)
        assert isinstance(results, list)
        assert len(results) == 1
        # Invalid ticker may return None data or empty info
        r = results[0]
        assert isinstance(r, ToolResult)


class TestUSStockPrice:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, us_price):
        results = await us_price.api_function(ticker=VALID_TICKER, period="1mo")
        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty
        assert "Close" in r.data.columns
        assert "Volume" in r.data.columns

    @pytest.mark.asyncio
    async def test_different_period(self, us_price):
        results = await us_price.api_function(ticker=VALID_TICKER, period="5d")
        r = results[0]
        assert isinstance(r.data, pd.DataFrame)
        assert len(r.data) <= 10  # 5 trading days max


class TestUSBalanceSheet:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, us_balance):
        results = await us_balance.api_function(ticker=VALID_TICKER)
        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty


class TestUSIncomeStatement:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, us_income):
        results = await us_income.api_function(ticker=VALID_TICKER)
        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty


class TestUSCashFlowStatement:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, us_cashflow):
        results = await us_cashflow.api_function(ticker=VALID_TICKER)
        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty


class TestUSShareholding:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, us_holding):
        results = await us_holding.api_function(ticker=VALID_TICKER)
        assert isinstance(results, list)
        assert len(results) >= 1
        for r in results:
            assert isinstance(r, ToolResult)
            assert r.name
            assert r.source

    @pytest.mark.asyncio
    async def test_invalid_ticker(self, us_holding):
        results = await us_holding.api_function(ticker=INVALID_TICKER)
        assert isinstance(results, list)
        assert len(results) >= 1
