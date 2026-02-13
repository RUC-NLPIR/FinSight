import datetime
import json
import requests

try:
    import akshare as ak
except ImportError:  # pragma: no cover - optional dependency
    ak = None
try:
    import efinance as ef
except ImportError:  # pragma: no cover - optional dependency
    ef = None
import pandas as pd
from bs4 import BeautifulSoup
try:
    import yfinance as yf
except ImportError:  # pragma: no cover - optional dependency
    yf = None

from ..base import Tool, ToolResult

# TODO: Add more granular Xueqiu endpoints (differentiate SH/SZ ahead of time).
class StockBasicInfo(Tool):
    def __init__(self):
        super().__init__(
            name="Stock profile",
            description="Return the basic corporate profile for a given ticker. Confirm the exchange-specific ticker before calling.",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK for Hong Kong, A for A-share, US for U.S. equities", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters for the tool call from the routing task.
        """
        if task.stock_code is None:
            # This should already be validated upstream
            assert False, "Stock code cannot be empty"
        else:
            return {"stock_code": task.stock_code, "market": task.market}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        Call the upstream API and return the corresponding dataset.
        """
        try:
            market = (market or "HK").upper()
            if market == "A":
                if ak is None:
                    raise ImportError("akshare is required for A-share profile data")
                data = ak.stock_zyjs_ths(symbol=stock_code)
            elif market == "HK":
                if ak is None:
                    raise ImportError("akshare is required for HK profile data")
                data = ak.stock_hk_company_profile_em(symbol=stock_code)
            elif market == "US":
                if yf is None:
                    raise ImportError("yfinance is required for US market profile data")
                info = yf.Ticker(stock_code).info or {}
                if not info or info.get("regularMarketPrice") is None:
                    data = None
                else:
                    data = {
                        "ticker": stock_code.upper(),
                        "name": info.get("shortName") or info.get("longName", ""),
                        "sector": info.get("sector", ""),
                        "industry": info.get("industry", ""),
                        "country": info.get("country", ""),
                        "market_cap": info.get("marketCap"),
                        "enterprise_value": info.get("enterpriseValue"),
                        "full_time_employees": info.get("fullTimeEmployees"),
                        "business_summary": info.get("longBusinessSummary", ""),
                    }
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK', 'A', or 'US'.")
        except Exception as e:
            print("Failed to fetch basic stock info", e)
            data = None
        return [
            ToolResult(
                name = f"{self.name}: {stock_code}",
                description = f"Corporate profile for {stock_code}.",
                data = data,
                source="Xueqiu: Stock basic information. https://xueqiu.com/S"
            )
        ]


class ShareHoldingStructure(Tool):
    def __init__(self):
        super().__init__(
            name="Shareholding structure",
            description="Return shareholder composition, including holder names, share counts, percentages, and equity type.",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK for Hong Kong, A for A-share, US for U.S. equities", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters for the tool call from the routing task.
        """
        if task.stock_code is None:
            # This should already be validated upstream
            assert False, "Stock code cannot be empty"
        else:
            return {"stock_code": task.stock_code, "market": task.market}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        Fetch the shareholder list for the given market and ticker.
        """
        try:
            market = (market or "HK").upper()
            if market == "A":
                if ak is None:
                    raise ImportError("akshare is required for A-share shareholding data")
                data = ak.stock_main_stock_holder(stock=stock_code)
            elif market == "HK":
                if ak is None:
                    raise ImportError("akshare is required for HK shareholding data")
                # Scrape data from Eastmoney — use the latest quarter-end date
                # instead of a hardcoded one so the data stays fresh.
                today = datetime.date.today()
                quarter_ends = [
                    datetime.date(today.year, 3, 31),
                    datetime.date(today.year, 6, 30),
                    datetime.date(today.year, 9, 30),
                    datetime.date(today.year, 12, 31),
                ]
                # Pick the most recent quarter-end that has already passed.
                past_ends = [d for d in quarter_ends if d <= today]
                if not past_ends:
                    # Before March 31 of the current year — use last year's Q4.
                    report_date = datetime.date(today.year - 1, 12, 31)
                else:
                    report_date = past_ends[-1]
                report_date_str = report_date.strftime("%Y-%m-%d")

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                output = requests.get(
                    f"https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_HKF10_EQUITYCHG_HOLDER&columns=SECURITY_CODE%2CSECUCODE%2CORG_CODE%2CNOTICE_DATE%2CREPORT_DATE%2CHOLDER_NAME%2CTOTAL_SHARES%2CTOTAL_SHARES_RATIO%2CDIRECT_SHARES%2CSHARES_CHG_RATIO%2CSHARES_TYPE%2CEQUITY_TYPE%2CHOLD_IDENTITY%2CIS_ZJ&quoteColumns=&filter=(SECUCODE%3D%22{stock_code}.HK%22)(REPORT_DATE%3D%27{report_date_str}%27)&pageNumber=1&pageSize=&sortTypes=-1%2C-1&sortColumns=EQUITY_TYPE%2CTOTAL_SHARES&source=F10&client=PC&v=032666133943694553",
                    headers = headers,
                )
                try:
                    html = output.text
                    output = json.loads(html)
                    data = output["result"]["data"]
                    data = pd.DataFrame(data)
                    data = data.rename(columns={
                        'HOLDER_NAME': 'holder_name',
                        'TOTAL_SHARES': 'shares',
                        'TOTAL_SHARES_RATIO': 'ownership_pct',
                        'DIRECT_SHARES': 'direct_shares',
                        'HOLD_IDENTITY': 'ownership_type',
                        'IS_ZJ': 'is_direct'
                    })
                    data = data.loc[:, ['holder_name', 'shares', 'ownership_pct', 'ownership_type', 'is_direct']]
                    data['is_direct'] = data['is_direct'].map({'1': 'Yes', '0': 'No'})
                    data.sort_values(by='ownership_pct', ascending=False, inplace=True)
                    data.reset_index(drop=True, inplace=True)
                except Exception as e:
                    print("Failed to parse Hong Kong shareholding structure", e)
                    data = None
            elif market == "US":
                if yf is None:
                    raise ImportError("yfinance is required for US shareholding data")
                ticker = yf.Ticker(stock_code)
                major_holders = ticker.major_holders
                institutional_holders = ticker.institutional_holders
                major_data = (
                    major_holders.to_dict(orient="records")
                    if major_holders is not None and not major_holders.empty
                    else []
                )
                institutional_data = (
                    institutional_holders.to_dict(orient="records")
                    if institutional_holders is not None and not institutional_holders.empty
                    else []
                )
                if not major_data and not institutional_data:
                    data = None
                else:
                    data = {
                        "ticker": stock_code.upper(),
                        "major_holders": major_data,
                        "institutional_holders": institutional_data,
                    }
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK', 'A', or 'US'.")
        except Exception as e:
            print("Failed to fetch shareholding structure", e)
            data = None
        return [
            ToolResult(
                name=f"{self.name} (ticker: {stock_code})",
                description=self.description,
                data=data,
                source="Sina Finance: Shareholder structure. https://vip.stock.finance.sina.com.cn/corp/go.php/vCI_StockHolder/stockid/600004.phtml"
            )
        ]

class StockBaseInfo(Tool):
    def __init__(self):
        super().__init__(
            name="Equity valuation metrics",
            description="Return valuation and profitability metrics such as PE, PB, ROE, and gross margin.",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK for Hong Kong, A for A-share, US for U.S. equities", "required": False},
            ],
        )

    def prepare_params(self, task) -> dict:
        return {"stock_code": task.stock_code, "market": getattr(task, "market", "HK")}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        Fetch fundamental metrics for the requested ticker.
        """
        try:
            market = (market or "HK").upper()
            if market in ("A", "HK"):
                if ef is None:
                    raise ImportError("efinance is required for A/HK valuation data")
                data = ef.stock.get_base_info(stock_code)
            elif market == "US":
                if yf is None:
                    raise ImportError("yfinance is required for US valuation data")
                info = yf.Ticker(stock_code).info or {}
                if not info or info.get("regularMarketPrice") is None:
                    data = None
                else:
                    data = {
                        "ticker": stock_code.upper(),
                        "trailing_pe": info.get("trailingPE"),
                        "forward_pe": info.get("forwardPE"),
                        "price_to_book": info.get("priceToBook"),
                        "return_on_equity": info.get("returnOnEquity"),
                        "gross_margins": info.get("grossMargins"),
                        "operating_margins": info.get("operatingMargins"),
                        "profit_margins": info.get("profitMargins"),
                        "beta": info.get("beta"),
                    }
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK', 'A', or 'US'.")
        except Exception as e:
            print("Failed to fetch stock valuation info", e)
            data = None
        return [
            ToolResult(
                name=f"{self.name} (ticker: {stock_code})",
                description=self.description,
                data=data,
                source="Exchange filings: Equity valuation metrics."
            )
        ]


class StockPrice(Tool):
    def __init__(self):
        super().__init__(
            name="Stock candlestick data",
            description="Daily OHLCV data including turnover and rate-of-change metrics.",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Ticker/Stock Code (support A-share and HK-share), e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK for Hong Kong, A for A-share, US for U.S. equities", "required": False},
                {"name": "period", "type": "str", "description": "US period for yfinance (e.g., 1mo, 3mo, 1y). Ignored for A/HK.", "required": False},
            ],
        )

    def prepare_params(self, task) -> dict:
        return {"stock_code": task.stock_code, "market": getattr(task, "market", "HK"), "period": "1y"}

    async def api_function(self, stock_code: str, market: str = "HK", period: str = "1y"):
        """
        Fetch historical quote data for the requested ticker.
        """
        try:
            market = (market or "HK").upper()
            if market in ("A", "HK"):
                if ef is None:
                    raise ImportError("efinance is required for A/HK price history")
                data = ef.stock.get_quote_history(stock_code)
            elif market == "US":
                if yf is None:
                    raise ImportError("yfinance is required for US price history")
                hist = yf.Ticker(stock_code).history(period=period)
                if hist is None or hist.empty:
                    data = None
                else:
                    hist = hist.reset_index()
                    keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in hist.columns]
                    data = hist[keep_cols].copy()
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK', 'A', or 'US'.")
        except Exception as e:
            print("Failed to fetch stock price history", e)
            data = None
        return [
            ToolResult(
                name=f"{self.name} (ticker: {stock_code})",
                description=self.description,
                data=data,
                source="Exchange trading data: OHLCV history."
            )
        ]