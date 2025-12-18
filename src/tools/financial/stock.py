import requests
import json
import akshare as ak
import pandas as pd
import efinance as ef
from bs4 import BeautifulSoup

from ..base import Tool, ToolResult

# TODO: Add more granular Xueqiu endpoints (differentiate SH/SZ ahead of time).
class StockBasicInfo(Tool):
    def __init__(self):
        super().__init__(
            name="Stock profile",
            description="Return the basic corporate profile for a given ticker. Confirm the exchange-specific ticker before calling.",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK for Hong Kong, A for A-share", "required": True},
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
            if market == "A":
                data = ak.stock_zyjs_ths(symbol=stock_code)
            elif market == "HK":
                data = ak.stock_hk_company_profile_em(symbol=stock_code)
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK' or 'A'.")
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
                {"name": "market", "type": "str", "description": "Market flag: HK for Hong Kong, A for A-share", "required": True},
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
            if market == "A":
                data = ak.stock_main_stock_holder(stock=stock_code)
            elif market == "HK":
                # Scrape data from Eastmoney
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                output = requests.get(
                    f"https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_HKF10_EQUITYCHG_HOLDER&columns=SECURITY_CODE%2CSECUCODE%2CORG_CODE%2CNOTICE_DATE%2CREPORT_DATE%2CHOLDER_NAME%2CTOTAL_SHARES%2CTOTAL_SHARES_RATIO%2CDIRECT_SHARES%2CSHARES_CHG_RATIO%2CSHARES_TYPE%2CEQUITY_TYPE%2CHOLD_IDENTITY%2CIS_ZJ&quoteColumns=&filter=(SECUCODE%3D%22{stock_code}.HK%22)(REPORT_DATE%3D%272024-12-31%27)&pageNumber=1&pageSize=&sortTypes=-1%2C-1&sortColumns=EQUITY_TYPE%2CTOTAL_SHARES&source=F10&client=PC&v=032666133943694553",
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
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK' or 'A'.")
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
            ],
        )

    def prepare_params(self, task) -> dict:
        return {"stock_code": task.stock_code}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        Fetch fundamental metrics for the requested ticker.
        """
        try:
            data = ef.stock.get_base_info(stock_code)
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
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        return {"stock_code": task.stock_code}

    async def api_function(self, stock_code: str, market: str = "HK"):
        """
        Fetch historical quote data for the requested ticker.
        """
        try:
            data = ef.stock.get_quote_history(stock_code)
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