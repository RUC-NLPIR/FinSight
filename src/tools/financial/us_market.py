"""US equity market data tools powered by yfinance.

These tools mirror the Chinese-market equivalents (stock.py, company_statements.py)
but target US-listed tickers (e.g. AAPL, TSLA, MSFT).
"""

import pandas as pd
import yfinance as yf

from ..base import Tool, ToolResult


class USStockProfile(Tool):
    def __init__(self):
        super().__init__(
            name="US Stock profile",
            description="Return the corporate profile for a US-listed ticker, including sector, industry, market cap, employees, and business summary.",
            parameters=[
                {"name": "ticker", "type": "str", "description": "US ticker symbol, e.g. AAPL", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        if task.stock_code is None:
            assert False, "Stock code cannot be empty"
        return {"ticker": task.stock_code}

    async def api_function(self, ticker: str):
        """Fetch company profile from Yahoo Finance."""
        try:
            t = yf.Ticker(ticker)
            info = t.info
            if not info or info.get("regularMarketPrice") is None:
                return [
                    ToolResult(
                        name=f"{self.name} ({ticker})",
                        description=f"No profile data found for {ticker}.",
                        data=None,
                        source=f"Yahoo Finance: {ticker}",
                    )
                ]

            profile = {
                "ticker": ticker,
                "name": info.get("shortName") or info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "country": info.get("country", ""),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "full_time_employees": info.get("fullTimeEmployees"),
                "business_summary": info.get("longBusinessSummary", ""),
            }
        except Exception as e:
            print(f"Failed to fetch US stock profile for {ticker}: {e}")
            profile = None

        return [
            ToolResult(
                name=f"{self.name} ({ticker})",
                description=f"Corporate profile for US ticker {ticker}.",
                data=profile,
                source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}",
            )
        ]


class USStockPrice(Tool):
    def __init__(self):
        super().__init__(
            name="US Stock price history",
            description="Return historical OHLCV price data for a US-listed ticker.",
            parameters=[
                {"name": "ticker", "type": "str", "description": "US ticker symbol, e.g. AAPL", "required": True},
                {"name": "period", "type": "str", "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max", "required": False},
            ],
        )

    def prepare_params(self, task) -> dict:
        if task.stock_code is None:
            assert False, "Stock code cannot be empty"
        return {"ticker": task.stock_code, "period": "1y"}

    async def api_function(self, ticker: str, period: str = "1y"):
        """Fetch historical price data from Yahoo Finance."""
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            if hist.empty:
                data = None
            else:
                # Reset index to make Date a column
                hist = hist.reset_index()
                # Keep only essential columns
                keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in hist.columns]
                data = hist[keep_cols].copy()
                # Round price columns
                for col in ["Open", "High", "Low", "Close"]:
                    if col in data.columns:
                        data[col] = data[col].round(2)
        except Exception as e:
            print(f"Failed to fetch US stock price for {ticker}: {e}")
            data = None

        return [
            ToolResult(
                name=f"{self.name} ({ticker}, {period})",
                description=f"Historical price data for {ticker} over {period}.",
                data=data,
                source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}/history",
            )
        ]


class USBalanceSheet(Tool):
    def __init__(self):
        super().__init__(
            name="US Balance sheet",
            description="Return the annual balance sheet for a US-listed ticker, with assets, liabilities, and equity (in millions USD).",
            parameters=[
                {"name": "ticker", "type": "str", "description": "US ticker symbol, e.g. AAPL", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        if task.stock_code is None:
            assert False, "Stock code cannot be empty"
        return {"ticker": task.stock_code}

    async def api_function(self, ticker: str):
        """Fetch annual balance sheet from Yahoo Finance."""
        try:
            t = yf.Ticker(ticker)
            bs = t.balance_sheet
            if bs is None or bs.empty:
                data = None
            else:
                # Transpose: rows=items, cols=years; values in millions
                data = bs.T.sort_index()
                data = (data / 1_000_000).round(2)
                data.index = data.index.strftime("%Y") if hasattr(data.index, "strftime") else data.index
                data = data.T  # items as rows, years as columns
                data.index.name = "Item (USD millions)"
                data = data.reset_index()
        except Exception as e:
            print(f"Failed to fetch US balance sheet for {ticker}: {e}")
            data = None

        return [
            ToolResult(
                name=f"{self.name} ({ticker})",
                description=f"Annual balance sheet for US ticker {ticker}.",
                data=data,
                source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}/financials",
            )
        ]


class USIncomeStatement(Tool):
    def __init__(self):
        super().__init__(
            name="US Income statement",
            description="Return the annual income statement for a US-listed ticker (revenue, costs, net income, in millions USD).",
            parameters=[
                {"name": "ticker", "type": "str", "description": "US ticker symbol, e.g. AAPL", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        if task.stock_code is None:
            assert False, "Stock code cannot be empty"
        return {"ticker": task.stock_code}

    async def api_function(self, ticker: str):
        """Fetch annual income statement from Yahoo Finance."""
        try:
            t = yf.Ticker(ticker)
            inc = t.income_stmt
            if inc is None or inc.empty:
                data = None
            else:
                data = inc.T.sort_index()
                data = (data / 1_000_000).round(2)
                data.index = data.index.strftime("%Y") if hasattr(data.index, "strftime") else data.index
                data = data.T
                data.index.name = "Item (USD millions)"
                data = data.reset_index()
        except Exception as e:
            print(f"Failed to fetch US income statement for {ticker}: {e}")
            data = None

        return [
            ToolResult(
                name=f"{self.name} ({ticker})",
                description=f"Annual income statement for US ticker {ticker}.",
                data=data,
                source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}/financials",
            )
        ]


class USCashFlowStatement(Tool):
    def __init__(self):
        super().__init__(
            name="US Cash-flow statement",
            description="Return the annual cash-flow statement for a US-listed ticker (operating, investing, financing, in millions USD).",
            parameters=[
                {"name": "ticker", "type": "str", "description": "US ticker symbol, e.g. AAPL", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        if task.stock_code is None:
            assert False, "Stock code cannot be empty"
        return {"ticker": task.stock_code}

    async def api_function(self, ticker: str):
        """Fetch annual cash-flow statement from Yahoo Finance."""
        try:
            t = yf.Ticker(ticker)
            cf = t.cashflow
            if cf is None or cf.empty:
                data = None
            else:
                data = cf.T.sort_index()
                data = (data / 1_000_000).round(2)
                data.index = data.index.strftime("%Y") if hasattr(data.index, "strftime") else data.index
                data = data.T
                data.index.name = "Item (USD millions)"
                data = data.reset_index()
        except Exception as e:
            print(f"Failed to fetch US cash-flow statement for {ticker}: {e}")
            data = None

        return [
            ToolResult(
                name=f"{self.name} ({ticker})",
                description=f"Annual cash-flow statement for US ticker {ticker}.",
                data=data,
                source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}/financials",
            )
        ]


class USShareholding(Tool):
    def __init__(self):
        super().__init__(
            name="US Shareholding structure",
            description="Return major and institutional holder information for a US-listed ticker.",
            parameters=[
                {"name": "ticker", "type": "str", "description": "US ticker symbol, e.g. AAPL", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        if task.stock_code is None:
            assert False, "Stock code cannot be empty"
        return {"ticker": task.stock_code}

    async def api_function(self, ticker: str):
        """Fetch institutional and major holders from Yahoo Finance."""
        results = []
        try:
            t = yf.Ticker(ticker)

            # Major holders (insiders vs institutions %)
            mh = t.major_holders
            if mh is not None and not mh.empty:
                results.append(
                    ToolResult(
                        name=f"Major holders ({ticker})",
                        description=f"Insider vs institutional ownership breakdown for {ticker}.",
                        data=mh,
                        source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}/holders",
                    )
                )

            # Top institutional holders
            ih = t.institutional_holders
            if ih is not None and not ih.empty:
                results.append(
                    ToolResult(
                        name=f"Institutional holders ({ticker})",
                        description=f"Top institutional holders of {ticker}.",
                        data=ih,
                        source=f"Yahoo Finance: https://finance.yahoo.com/quote/{ticker}/holders",
                    )
                )
        except Exception as e:
            print(f"Failed to fetch US shareholding for {ticker}: {e}")

        if not results:
            results.append(
                ToolResult(
                    name=f"Shareholding ({ticker})",
                    description=f"No holder data found for {ticker}.",
                    data=None,
                    source=f"Yahoo Finance: {ticker}",
                )
            )

        return results
