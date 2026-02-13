"""US macroeconomic data tools.

Provides tools for US macro indicators using:
- yfinance: for market index data (S&P 500, DJIA, NASDAQ)
- fredapi: for FRED economic series (CPI, GDP, Unemployment, Interest Rates)

The FRED tools require a ``FRED_API_KEY`` environment variable. If the key
is missing the tools will still instantiate but return an error ToolResult
when called, allowing the agent to gracefully degrade.
"""

import os

import pandas as pd

from ..base import Tool, ToolResult

# Lazy-loaded to avoid import-time failures
_fred = None


def _get_fred():
    """Return a cached ``Fred`` client, or ``None`` if the key is not set."""
    global _fred
    if _fred is not None:
        return _fred
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return None
    try:
        from fredapi import Fred
        _fred = Fred(api_key=api_key)
        return _fred
    except Exception:
        return None


class USCPI(Tool):
    def __init__(self):
        super().__init__(
            name="US CPI (FRED)",
            description="US Consumer Price Index for All Urban Consumers (CPIAUCSL) from FRED. Monthly, seasonally adjusted.",
            parameters=[
                {"name": "start", "type": "str", "description": "Start date YYYY-MM-DD (default: 10 years ago)", "required": False},
            ],
        )

    async def api_function(self, start: str = None):
        fred = _get_fred()
        if fred is None:
            return [ToolResult(
                name=self.name, description="FRED_API_KEY not set",
                data=None, source="FRED: CPIAUCSL",
            )]
        try:
            if start is None:
                import datetime
                start = (datetime.date.today() - datetime.timedelta(days=365 * 10)).isoformat()
            series = fred.get_series("CPIAUCSL", observation_start=start)
            data = pd.DataFrame({"date": series.index, "CPI": series.values})
        except Exception as e:
            print(f"Failed to fetch FRED CPI: {e}")
            data = None
        return [ToolResult(
            name=self.name, description="US CPI (All Urban, SA)",
            data=data, source="FRED: CPIAUCSL — https://fred.stlouisfed.org/series/CPIAUCSL",
        )]


class USGDP(Tool):
    def __init__(self):
        super().__init__(
            name="US GDP (FRED)",
            description="US Gross Domestic Product (GDP) from FRED. Quarterly, seasonally adjusted annual rate.",
            parameters=[
                {"name": "start", "type": "str", "description": "Start date YYYY-MM-DD (default: 20 years ago)", "required": False},
            ],
        )

    async def api_function(self, start: str = None):
        fred = _get_fred()
        if fred is None:
            return [ToolResult(
                name=self.name, description="FRED_API_KEY not set",
                data=None, source="FRED: GDP",
            )]
        try:
            if start is None:
                import datetime
                start = (datetime.date.today() - datetime.timedelta(days=365 * 20)).isoformat()
            series = fred.get_series("GDP", observation_start=start)
            data = pd.DataFrame({"date": series.index, "GDP_billions": series.values})
        except Exception as e:
            print(f"Failed to fetch FRED GDP: {e}")
            data = None
        return [ToolResult(
            name=self.name, description="US GDP (SAAR, billions USD)",
            data=data, source="FRED: GDP — https://fred.stlouisfed.org/series/GDP",
        )]


class USUnemployment(Tool):
    def __init__(self):
        super().__init__(
            name="US Unemployment rate (FRED)",
            description="US Civilian Unemployment Rate (UNRATE) from FRED. Monthly, seasonally adjusted.",
            parameters=[
                {"name": "start", "type": "str", "description": "Start date YYYY-MM-DD (default: 10 years ago)", "required": False},
            ],
        )

    async def api_function(self, start: str = None):
        fred = _get_fred()
        if fred is None:
            return [ToolResult(
                name=self.name, description="FRED_API_KEY not set",
                data=None, source="FRED: UNRATE",
            )]
        try:
            if start is None:
                import datetime
                start = (datetime.date.today() - datetime.timedelta(days=365 * 10)).isoformat()
            series = fred.get_series("UNRATE", observation_start=start)
            data = pd.DataFrame({"date": series.index, "unemployment_rate_pct": series.values})
        except Exception as e:
            print(f"Failed to fetch FRED Unemployment: {e}")
            data = None
        return [ToolResult(
            name=self.name, description="US Unemployment Rate (%)",
            data=data, source="FRED: UNRATE — https://fred.stlouisfed.org/series/UNRATE",
        )]


class USInterestRates(Tool):
    def __init__(self):
        super().__init__(
            name="US Interest rates (FRED)",
            description="US key interest rates: Fed Funds Rate (FEDFUNDS), 10-Year Treasury (DGS10), 2-Year Treasury (DGS2).",
            parameters=[
                {"name": "start", "type": "str", "description": "Start date YYYY-MM-DD (default: 10 years ago)", "required": False},
            ],
        )

    async def api_function(self, start: str = None):
        fred = _get_fred()
        if fred is None:
            return [ToolResult(
                name=self.name, description="FRED_API_KEY not set",
                data=None, source="FRED",
            )]
        try:
            import datetime
            if start is None:
                start = (datetime.date.today() - datetime.timedelta(days=365 * 10)).isoformat()
            series_ids = {"FEDFUNDS": "fed_funds_rate", "DGS10": "treasury_10y", "DGS2": "treasury_2y"}
            frames = []
            for sid, col in series_ids.items():
                s = fred.get_series(sid, observation_start=start)
                frames.append(pd.DataFrame({"date": s.index, col: s.values}))
            data = frames[0]
            for f in frames[1:]:
                data = data.merge(f, on="date", how="outer")
            data = data.sort_values("date").reset_index(drop=True)
        except Exception as e:
            print(f"Failed to fetch FRED interest rates: {e}")
            data = None
        return [ToolResult(
            name=self.name, description="US Key Interest Rates",
            data=data, source="FRED: FEDFUNDS, DGS10, DGS2 — https://fred.stlouisfed.org",
        )]


class USMarketIndex(Tool):
    def __init__(self):
        super().__init__(
            name="US Market index",
            description="US major market index OHLCV data: S&P 500 (^GSPC), DJIA (^DJI), or NASDAQ (^IXIC) via Yahoo Finance.",
            parameters=[
                {"name": "index_symbol", "type": "str", "description": "Yahoo Finance index symbol: ^GSPC, ^DJI, or ^IXIC", "required": True},
                {"name": "period", "type": "str", "description": "Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y, max", "required": False},
            ],
        )

    async def api_function(self, index_symbol: str = "^GSPC", period: str = "1y"):
        try:
            import yfinance as yf
            t = yf.Ticker(index_symbol)
            hist = t.history(period=period)
            if hist.empty:
                data = None
            else:
                hist = hist.reset_index()
                keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in hist.columns]
                data = hist[keep_cols].copy()
                for col in ["Open", "High", "Low", "Close"]:
                    if col in data.columns:
                        data[col] = data[col].round(2)
        except Exception as e:
            print(f"Failed to fetch US market index {index_symbol}: {e}")
            data = None

        index_names = {"^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ Composite"}
        display_name = index_names.get(index_symbol, index_symbol)

        return [ToolResult(
            name=f"{display_name} ({period})",
            description=f"{display_name} index OHLCV data for {period}.",
            data=data,
            source=f"Yahoo Finance: https://finance.yahoo.com/quote/{index_symbol}",
        )]
