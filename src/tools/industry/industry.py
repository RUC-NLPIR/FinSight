import akshare as ak
import pandas as pd
from ..base import Tool, ToolResult


class Industry_gyzjz(Tool):
    def __init__(self):
        super().__init__(
            name = "Industrial value-added growth",
            description = "China industrial value-added growth from 2008 onward (Eastmoney).",
            parameters = [],
        ) 
        
    async def api_function(self):
        data = ak.macro_china_gyzjz()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Industrial value-added growth. https://data.eastmoney.com/cjsj/gyzjz.html",
            )
        ]
        
class Industry_production_yoy(Tool):
    def __init__(self):
        super().__init__(
            name = "Above-scale industrial production YoY",
            description = "China's YoY industrial production growth for enterprises above designated size, from 1990 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_industrial_production_yoy()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Above-scale industrial production YoY. https://datacenter.jin10.com/reportType/dc_chinese_industrial_production_yoy",
            )
        ]
        
class Industry_China_PMI(Tool):
    def __init__(self):
        super().__init__(
            name = "Official manufacturing PMI",
            description = "China's official manufacturing PMI series from 2005 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_pmi_yearly()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Official manufacturing PMI. https://datacenter.jin10.com/reportType/dc_chinese_manufacturing_pmi",
            )
        ]
        
class Industry_China_CX_services_PMI(Tool):
    def __init__(self):
        super().__init__(
            name = "Caixin services PMI",
            description = "China's Caixin services PMI report from 2012 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_cx_services_pmi_yearly()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Caixin services PMI. https://datacenter.jin10.com/reportType/dc_chinese_caixin_services_pmi",
            )
        ]
        
class Industry_China_CPI(Tool):
    def __init__(self):
        super().__init__(
            name = "Consumer price index",
            description = "Monthly CPI data for China from 2008 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_cpi()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Consumer price index. http://data.eastmoney.com/cjsj/cpi.html",
            )
        ]
        
class Industry_China_GDP(Tool):
    def __init__(self):
        super().__init__(
            name = "Gross domestic product",
            description = "Monthly GDP-related statistics for China from 2006 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_gdp()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Gross domestic product. http://data.eastmoney.com/cjsj/gdp.html",
            )
        ]
        
class Industry_China_PPI(Tool):
    def __init__(self):
        super().__init__(
            name = "Producer price index",
            description = "Monthly producer price index (ex-factory) for China from 2006 onward.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_ppi()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Producer price index. http://data.eastmoney.com/cjsj/ppi.html",
            )
        ]
        
class Industry_China_xfzxx(Tool):
    def __init__(self):
        super().__init__(
            name = "Consumer confidence index",
            description = "Historical consumer confidence index with YoY and MoM changes (Eastmoney).",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_xfzxx()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Consumer confidence index. https://data.eastmoney.com/cjsj/xfzxx.html",
            )
        ]
        
class Industry_China_consumer_goods_retail(Tool):
    def __init__(self):
        super().__init__(
            name = "Total retail sales of consumer goods",
            description = "Historical stats for total retail sales of consumer goods with YoY and MoM changes.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_consumer_goods_retail()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Total retail sales of consumer goods. http://data.eastmoney.com/cjsj/xfp.html",
            )
        ]
        
class Industry_China_retail_price_index(Tool):
    def __init__(self):
        super().__init__(
            name = "Retail price index",
            description = "Historical retail price index from the National Bureau of Statistics.",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_retail_price_index()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Sina Finance: Retail price index. http://finance.sina.com.cn/mac/#price-12-0-31-1",
            )
        ]
        
class Industry_China_qyspjg(Tool):
    def __init__(self):
        super().__init__(
            name = "Enterprise commodity price index",
            description = "Enterprise commodity price index series from 2005 onward (Eastmoney).",
            parameters = [],
        )
        
    async def api_function(self):
        data = ak.macro_china_qyspjg()
        return [
            ToolResult(
                name=self.name,
                description=self.description,
                data=data,
                source="Eastmoney: Enterprise commodity price index. http://data.eastmoney.com/cjsj/qyspjg.html",
            )
        ]