"""Tests for US support inside existing financial tool classes.

Maintainer feedback requested that US functionality should be merged into
existing classes and switched by ``market='US'`` instead of dedicated
``US*`` tool classes.
"""

import pandas as pd
import pytest

from src.tools.base import ToolResult
from src.tools.financial.company_statements import (
    BalanceSheet,
    CashFlowStatement,
    IncomeStatement,
)
from src.tools.financial.stock import ShareHoldingStructure, StockBasicInfo, StockPrice


VALID_TICKER = "AAPL"
INVALID_TICKER = "ZZZZZZZNOTREAL123"


@pytest.fixture
def profile_tool():
    return StockBasicInfo()


@pytest.fixture
def price_tool():
    return StockPrice()


@pytest.fixture
def balance_tool():
    return BalanceSheet()


@pytest.fixture
def income_tool():
    return IncomeStatement()


@pytest.fixture
def cashflow_tool():
    return CashFlowStatement()


@pytest.fixture
def holding_tool():
    return ShareHoldingStructure()


class TestToolMetadata:
    def test_existing_names_unchanged(self, profile_tool, price_tool, balance_tool, income_tool, cashflow_tool, holding_tool):
        assert profile_tool.name == "Stock profile"
        assert price_tool.name == "Stock candlestick data"
        assert balance_tool.name == "Balance sheet"
        assert income_tool.name == "Income statement"
        assert cashflow_tool.name == "Cash-flow statement"
        assert holding_tool.name == "Shareholding structure"


class TestUSProfileViaMarketFlag:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, profile_tool):
        results = await profile_tool.api_function(stock_code=VALID_TICKER, market="US")
        assert isinstance(results, list) and len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, dict)
        assert r.data["ticker"] == VALID_TICKER

    @pytest.mark.asyncio
    async def test_invalid_ticker(self, profile_tool):
        results = await profile_tool.api_function(stock_code=INVALID_TICKER, market="US")
        assert isinstance(results, list) and len(results) == 1
        assert isinstance(results[0], ToolResult)


class TestUSPriceViaMarketFlag:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, price_tool):
        results = await price_tool.api_function(stock_code=VALID_TICKER, market="US", period="1mo")
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty
        assert "Close" in r.data.columns


class TestUSStatementsViaMarketFlag:
    @pytest.mark.asyncio
    async def test_balance_sheet(self, balance_tool):
        results = await balance_tool.api_function(stock_code=VALID_TICKER, market="US")
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty

    @pytest.mark.asyncio
    async def test_income_statement(self, income_tool):
        results = await income_tool.api_function(stock_code=VALID_TICKER, market="US")
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty

    @pytest.mark.asyncio
    async def test_cashflow_statement(self, cashflow_tool):
        results = await cashflow_tool.api_function(stock_code=VALID_TICKER, market="US")
        r = results[0]
        assert isinstance(r, ToolResult)
        assert isinstance(r.data, pd.DataFrame)
        assert not r.data.empty


class TestUSShareholdingViaMarketFlag:
    @pytest.mark.asyncio
    async def test_valid_ticker(self, holding_tool):
        results = await holding_tool.api_function(stock_code=VALID_TICKER, market="US")
        assert isinstance(results, list) and len(results) == 1
        r = results[0]
        assert isinstance(r, ToolResult)
        # Depending on upstream availability, data can be dict or None.
        assert isinstance(r.data, (dict, type(None)))
