import akshare as ak
import pandas as pd
from ..base import Tool, ToolResult


class HuShen_Index(Tool):
    def __init__(self):
        super().__init__(
            name="CSI 300 daily data",
            description="Daily CSI 300 index data, including OHLC, volume, turnover, returns, and turnover ratio.",
            parameters=[]
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task (none required here).
        """
        return {}

    async def api_function(self):
        """
        Fetch the CSI 300 time series.
        """
        try:
            data = ak.stock_zh_index_daily(symbol="sh000300")
        except Exception as e:
            print("Failed to fetch CSI 300 data", e)
            data = None
        if data is not None:
            return [
                ToolResult(
                    name = f"{self.name}",
                    description = self.description,
                    data = data,
                    source="Sina Finance: CSI 300 daily data. https://finance.sina.com.cn/realstock/company/sz000300/nc.shtml"
                )
            ]
        else:
            return []


class HengSheng_Index(Tool):
    def __init__(self):
        super().__init__(
            name="Hang Seng Index daily data",
            description="Daily Hang Seng Index data including OHLC, volume, turnover, returns, and turnover ratio.",
            parameters=[]
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task (none required here).
        """
        return {}

    async def api_function(self):
        """
        Fetch the Hang Seng Index time series.
        """
        try:
            data = ak.stock_hk_index_daily_sina(symbol="HSI")
        except Exception as e:
            print("Failed to fetch Hang Seng data", e)
            data = None
        if data is not None:
            return [
                ToolResult(
                    name = f"{self.name}",
                    description = self.description,
                    data = data,
                    source="Sina Finance: Hang Seng Index daily data. https://stock.finance.sina.com.cn/hkstock/quotes/HSI.html."
                )
            ]
        else:
            return []
        
class ShangZheng_Index(Tool):
    def __init__(self):
        super().__init__(
            name="SSE Composite daily data",
            description="Daily Shanghai Composite index data with OHLC, volume, turnover, returns, and turnover ratio.",
            parameters=[]
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task (none required here).
        """
        return {}

    async def api_function(self):
        """
        Fetch the SSE Composite time series.
        """
        try:
            data = ak.stock_zh_index_daily(symbol="sh000001")
        except Exception as e:
            print("Failed to fetch SSE Composite data", e)
            data = None
        if data is not None:
            return [
                ToolResult(
                    name = f"{self.name}",
                    description = self.description,
                    data = data,
                    source="Sina Finance: SSE Composite daily data. https://finance.sina.com.cn/realstock/company/sz000001/nc.shtml"
                )
            ]
        else:
            return []


class NSDK_Index(Tool):
    def __init__(self):
        super().__init__(
            name="Nasdaq Composite daily data",
            description="Daily Nasdaq Composite data covering OHLC, volume, turnover, returns, and turnover ratio.",
            parameters=[]
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task (none required here).
        """
        return {}

    async def api_function(self):
        """
        Fetch the Nasdaq Composite time series.
        """
        try:
            data = ak.index_us_stock_sina(symbol=".IXIC")
        except Exception as e:
            print("Failed to fetch Nasdaq data", e)
            data = None
        if data is not None:
            return [
                ToolResult(
                    name = f"{self.name}",
                    description = self.description,
                    data = data,
                    source="Sina Finance: Nasdaq Composite daily data. https://stock.finance.sina.com.cn/usstock/quotes/.IXIC.html"
                )
            ]
        else:
            return []