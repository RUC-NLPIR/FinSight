import akshare as ak
import pandas as pd
from ..base import Tool, ToolResult


class Macro_China_Leverage_Ratio(Tool):
    def __init__(self):
        super().__init__(
            name = "China macro leverage ratio",
            description = "Historical leverage ratios for households, non-financial corporates, government, and financial sectors in China.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_cnbs()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "National Finance and Development Lab: China macro leverage ratio. http://114.115.232.154:8080/"
            )
        ]
        
class Macro_China_qyspjg(Tool):
    def __init__(self):
        super().__init__(
            name = "Enterprise commodity price index",
            description = "China's enterprise commodity price index from 2005 onward, covering aggregate, agricultural, mineral, and energy sub-indices with YoY/MoM changes.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_qyspjg()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: Enterprise commodity price index. http://data.eastmoney.com/cjsj/qyspjg.html"
            )
        ]
        
class Macro_China_LPR(Tool):
    def __init__(self):
        super().__init__(
            name = "China LPR benchmark rates",
            description = "Loan Prime Rate time series from 1991 onward, including 1Y, 5Y, and benchmark short-/long-term lending rates.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_lpr()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: LPR benchmark dataset. https://data.eastmoney.com/cjsj/globalRateLPR.html"
            )
        ]
    
class Macro_China_urban_unemployment(Tool):
    def __init__(self):
        super().__init__(
            name = "Urban surveyed unemployment rate",
            description = "Historical surveyed unemployment rate across Chinese urban areas, broken down by age groups and other categories.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_urban_unemployment()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "National Bureau of Statistics: Urban surveyed unemployment rate. https://data.stats.gov.cn/easyquery.htm?cn=A01&zb=A0203&sj=202304"
            )
        ]
        
class Macro_China_shrzgm(Tool):
    def __init__(self):
        super().__init__(
            name = "Total social financing increment",
            description = "Incremental total social financing data since 2015, covering RMB loans, entrusted loans, trust loans, bankers' acceptances, corporate bonds, and onshore equity financing.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_shrzgm()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Ministry of Commerce Data Center: Total social financing increment. http://data.mofcom.gov.cn/gnmy/shrzgm.shtml"
            )
        ]
        
class Macro_China_GDP_yearly(Tool):
    def __init__(self):
        super().__init__(
            name = "China GDP YoY",
            description = "China GDP year-over-year growth report, covering 2010 to present.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_gdp_yearly()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Jin10 Data Center: China GDP YoY. https://datacenter.jin10.com/reportType/dc_chinese_gdp_yoy"
            )
        ]
        
class Macro_China_CPI_yearly(Tool):
    def __init__(self):
        super().__init__(
            name = "China CPI YoY",
            description = "Annual CPI time series for China from 1986 to present.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_cpi_yearly()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Jin10 Data Center: China CPI YoY. https://datacenter.jin10.com/reportType/dc_chinese_cpi_yoy"
            )
        ]
        
class Macro_China_PPI_yearly(Tool):
    def __init__(self):
        super().__init__(
            name = "China PPI YoY",
            description = "Annual PPI time series for China from 1995 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_ppi_yearly()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Jin10 Data Center: China PPI YoY. https://datacenter.jin10.com/reportType/dc_chinese_ppi_yoy"
            )
        ]
        
class Macro_USA_CPI_yearly(Tool):
    def __init__(self):
        super().__init__(
            name = "US CPI YoY",
            description = "Annual CPI report for the United States from 2008 to present.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_usa_cpi_yoy()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: US CPI YoY report. https://data.eastmoney.com/cjsj/foreign_0_12.html"
            )
        ]
        
class Macro_China_exports_yearly(Tool):
    def __init__(self):
        super().__init__(
            name = "China exports YoY (USD)",
            description = "Year-over-year export growth for China measured in USD, from 1982 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_exports_yoy()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Jin10 Data Center: China exports YoY (USD). https://datacenter.jin10.com/reportType/dc_chinese_exports_yoy"
            )
        ]

class Macro_China_imports_yearly(Tool):
    def __init__(self):
        super().__init__(
            name = "China imports YoY (USD)",
            description = "Year-over-year import growth for China measured in USD, from 1996 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_imports_yoy()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Jin10 Data Center: China imports YoY (USD). https://datacenter.jin10.com/reportType/dc_chinese_imports_yoy"
            )
        ]

class Macro_China_trade_balance(Tool):
    def __init__(self):
        super().__init__(
            name = "China trade balance (USD bn)",
            description = "China's trade balance expressed in USD billions, from 1981 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_trade_balance()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Jin10 Data Center: China trade balance (USD bn). https://datacenter.jin10.com/reportType/dc_chinese_trade_balance"
            )
        ]

class Macro_China_czsr(Tool):
    def __init__(self):
        super().__init__(
            name = "Fiscal revenue",
            description = "Monthly fiscal revenue data for China from 2008 to present.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_czsr()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: Fiscal revenue. http://data.eastmoney.com/cjsj/czsr.html"
            )
        ]
        
class Macro_China_whxd(Tool):
    def __init__(self):
        super().__init__(
            name = "Foreign-exchange loan data",
            description = "Monthly FX loan balances for China since 2008, including YoY and MoM change metrics.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_whxd()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: Foreign-exchange loan data. http://data.eastmoney.com/cjsj/whxd.html"
            )
        ]

class Macro_China_bond_public(Tool):
    def __init__(self):
        super().__init__(
            name = "New bond issuance",
            description = "Recent bond issuance statistics; prices are quoted in CNY and planned size in 100 million CNY.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_bond_public()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "China Foreign Exchange Trade System: Recent bond issuance. https://www.chinamoney.com.cn/chinese/xzjfx/"
            )
        ]

class Macro_China_bank_balance(Tool):
    def __init__(self):
        super().__init__(
            name = "Central bank balance sheet",
            description = "People's Bank of China balance sheet statistics.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_central_bank_balance()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Sina Finance: Central bank balance sheet. http://finance.sina.com.cn/mac/#fininfo-8-0-31-2"
            )
        ]
        
class Macro_China_supply_of_money(Tool):
    def __init__(self):
        super().__init__(
            name = "Money supply",
            description = "Chinese monetary aggregates (M0/M1/M2) time series.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_supply_of_money()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Sina Finance: Money supply. http://finance.sina.com.cn/mac/#fininfo-1-0-31-1"
            )
        ]
        
class Macro_China_reserve_requirement_ratio(Tool):
    def __init__(self):
        super().__init__(
            name = "Reserve requirement ratio",
            description = "Statutory reserve requirement ratios for Chinese financial institutions.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_reserve_requirement_ratio()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: Reserve requirement ratio. https://data.eastmoney.com/cjsj/ckzbj.html"
            )
        ]

class Macro_China_fx_gold(Tool):
    def __init__(self):
        super().__init__(
            name = "FX and gold reserves",
            description = "Monthly foreign-exchange and gold reserve balances for China since 2008.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_fx_gold()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: FX and gold reserves. http://data.eastmoney.com/cjsj/hjwh.html"
            )
        ]

class Macro_China_stock_market_cap(Tool):
    def __init__(self):
        super().__init__(
            name = "National stock trading statistics",
            description = "Monthly nationwide stock-trading statistics from 2008 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_stock_market_cap()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Eastmoney: National stock trading statistics. http://data.eastmoney.com/cjsj/gpjytj.html"
            )
        ]

class Macro_China_epu_index(Tool):
    def __init__(self):
        super().__init__(
            name = "Economic policy uncertainty (China)",
            description = "Monthly economic policy uncertainty (EPU) index for China.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.article_epu_index(symbol="China")
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source = "Economic Policy Uncertainty: Economic Policy Uncertainty Index. https://www.policyuncertainty.com/index.html"
            )
        ]