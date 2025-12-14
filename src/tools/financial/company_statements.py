import akshare as ak
import pandas as pd
from ..base import Tool, ToolResult

def preprocess_balance_data(data: pd.DataFrame) -> pd.DataFrame:
    data.drop(['SECUCODE','SECURITY_CODE','SECURITY_NAME_ABBR','ORG_CODE', 'DATE_TYPE_CODE', 'FISCAL_YEAR','STD_ITEM_CODE','REPORT_DATE'], axis=1, inplace=True)
    data['YEAR'] = data['STD_REPORT_DATE'].apply(lambda x: pd.to_datetime(x).year)
    data.drop(['STD_REPORT_DATE'], axis=1, inplace=True)
    pd.set_option('display.float_format', '{:.2f}'.format) 
    data['AMOUNT'] = data['AMOUNT'].apply(lambda x: float(x)//1000000)

    item_order = {item: idx for idx, item in enumerate(data['STD_ITEM_NAME'].unique())}

    pivot_df = data.pivot_table(
        index='STD_ITEM_NAME',
        columns='YEAR',
        values='AMOUNT',
        aggfunc='sum'
    ).reset_index()

    pivot_df.columns.name = None
    pivot_df['original_order'] = pivot_df['STD_ITEM_NAME'].map(item_order)
    pivot_df = pivot_df.sort_values('original_order').drop(columns='original_order')

    year_cols = sorted([col for col in pivot_df.columns if col != 'STD_ITEM_NAME'])
    pivot_df = pivot_df[['STD_ITEM_NAME'] + year_cols]

    pivot_df['nan_count'] = pivot_df.iloc[:, 1:].isna().sum(axis=1)
    filtered_df = pivot_df[pivot_df['nan_count'] <= 3].copy()
    filtered_df.drop(columns='nan_count', inplace=True)

    filtered_df.reset_index(drop=True, inplace=True)

    filtered_df = filtered_df.rename(columns={'STD_ITEM_NAME': '类目'})
    use_columns = ['类目'] + [col for col in filtered_df.columns if col != '类目'][-5:]
    filtered_df = filtered_df.loc[:, use_columns]
    filtered_df['类目'] = filtered_df['类目'].apply(lambda x: f"**{x}**" if x.startswith('总') else x)
    return filtered_df


def preprocess_income_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess income-statement data into a pivot table.
    """
    data.drop(['SECUCODE','SECURITY_CODE','SECURITY_NAME_ABBR','ORG_CODE', 'DATE_TYPE_CODE', 'FISCAL_YEAR','STD_ITEM_CODE','REPORT_DATE'], axis=1, inplace=True)
    data['YEAR'] = data['START_DATE'].apply(lambda x: pd.to_datetime(x).year)
    data.drop(['START_DATE'], axis=1, inplace=True)
    pd.set_option('display.float_format', '{:.2f}'.format) 
    data['AMOUNT'] = data['AMOUNT'].apply(lambda x: float(x)//1000000)

    item_order = {item: idx for idx, item in enumerate(data['STD_ITEM_NAME'].unique())}

    pivot_df = data.pivot_table(
        index='STD_ITEM_NAME',
        columns='YEAR',
        values='AMOUNT',
        aggfunc='sum'
    ).reset_index()

    pivot_df.columns.name = None
    pivot_df['original_order'] = pivot_df['STD_ITEM_NAME'].map(item_order)
    pivot_df = pivot_df.sort_values('original_order').drop(columns='original_order')

    year_cols = sorted([col for col in pivot_df.columns if col != 'STD_ITEM_NAME'])
    pivot_df = pivot_df[['STD_ITEM_NAME'] + year_cols]

    pivot_df['nan_count'] = pivot_df.iloc[:, 1:].isna().sum(axis=1)
    filtered_df = pivot_df[pivot_df['nan_count'] <= 3].copy()
    filtered_df.drop(columns='nan_count', inplace=True)

    filtered_df.reset_index(drop=True, inplace=True)

    filtered_df = filtered_df.rename(columns={'STD_ITEM_NAME': '类目'})
    use_columns = ['类目'] + [col for col in filtered_df.columns if col != '类目'][-5:]
    filtered_df = filtered_df.loc[:, use_columns]
    filtered_df['类目'] = filtered_df['类目'].apply(lambda x: f"**{x}**" if x.startswith('总') else x)
    return filtered_df

class BalanceSheet(Tool):
    def __init__(self):
        super().__init__(
            name = "Balance sheet",
            description = "Returns the balance sheet covering assets, liabilities, and shareholders' equity for a given ticker.",
            parameters = [
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK or A", "required": True},
                {"name": "period", "type": "str", "description": "Reporting period (defaults to annual)", "required": False},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task.
        """
        if task.stock_code is None:
            # Should already be populated by the router
            assert False, "Stock code cannot be empty"
        else:
            return {"stock_code": task.stock_code, "market": task.market, "period": "annual"}
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the raw balance-sheet dataframe into a cleaner pivot table.
        """
        data.drop(['SECUCODE','SECURITY_CODE','SECURITY_NAME_ABBR','ORG_CODE', 'DATE_TYPE_CODE', 'FISCAL_YEAR','STD_ITEM_CODE','REPORT_DATE'], axis=1, inplace=True)
        data['YEAR'] = data['STD_REPORT_DATE'].apply(lambda x: pd.to_datetime(x).year)
        data.drop(['STD_REPORT_DATE'], axis=1, inplace=True)
        pd.set_option('display.float_format', '{:.2f}'.format) 
        data['AMOUNT'] = data['AMOUNT'].apply(lambda x: float(x)//1000000)

        item_order = {item: idx for idx, item in enumerate(data['STD_ITEM_NAME'].unique())}

        pivot_df = data.pivot_table(
            index='STD_ITEM_NAME',
            columns='YEAR',
            values='AMOUNT',
            aggfunc='sum'
        ).reset_index()

        pivot_df.columns.name = None
        pivot_df['original_order'] = pivot_df['STD_ITEM_NAME'].map(item_order)
        pivot_df = pivot_df.sort_values('original_order').drop(columns='original_order')

        year_cols = sorted([col for col in pivot_df.columns if col != 'STD_ITEM_NAME'])
        pivot_df = pivot_df[['STD_ITEM_NAME'] + year_cols]

        pivot_df['nan_count'] = pivot_df.iloc[:, 1:].isna().sum(axis=1)
        filtered_df = pivot_df[pivot_df['nan_count'] <= 3].copy()
        filtered_df.drop(columns='nan_count', inplace=True)

        filtered_df.reset_index(drop=True, inplace=True)

        filtered_df = filtered_df.rename(columns={'STD_ITEM_NAME': '会计年度 (人民币百万)'})
        use_columns = ['会计年度 (人民币百万)'] + [col for col in filtered_df.columns if col != '会计年度 (人民币百万)'][-5:]
        filtered_df = filtered_df.loc[:, use_columns]
        filtered_df['会计年度 (人民币百万)'] = filtered_df['会计年度 (人民币百万)'].apply(lambda x: f"**{x}**" if x.startswith('总') else x)
        return filtered_df

        

    async def api_function(self, stock_code: str, market: str = "HK", period: str = "年度"):
        """
        Fetch the balance sheet for the requested ticker.
        """
        period = "年度"
        try:
            if market == "HK":
                data = ak.stock_financial_hk_report_em(
                    stock = stock_code,
                    symbol = "资产负债表",
                    indicator = period,
                )
                try:
                    data = self._preprocess_data(data)
                except Exception as e:
                    print("Failed to preprocess balance-sheet data", e)
            elif market == "A":
                data = ak.stock_balance_sheet_by_yearly_em(
                    symbol = stock_code,
                )
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK' or 'A'.")
        except Exception as e:
            print("Failed to fetch balance sheet", e)
            data = None
        return [
            ToolResult(
                name = f"{self.name} (ticker: {stock_code})",
                description = f"Balance sheet for ticker {stock_code}.",
                data = data,
                source=f"Eastmoney financials: balance sheet for {stock_code}. https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code={stock_code}#lrb-0."
            )
        ]

class IncomeStatement(Tool):
    def __init__(self):
        super().__init__(
            name = "Income statement",
            description = "Returns the income statement detailing revenue, costs, expenses, and earnings for a given ticker.",
            parameters = [
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK or A", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task.
        """
        if task.stock_code is None:
            # Should already be populated by the router
            assert False, "Stock code cannot be empty"
        else:
            return {"stock_code": task.stock_code, "market": task.market, "period": "annual"}

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the raw income-statement dataframe into a cleaner pivot table.
        """
        data.drop(['SECUCODE','SECURITY_CODE','SECURITY_NAME_ABBR','ORG_CODE', 'DATE_TYPE_CODE', 'FISCAL_YEAR','STD_ITEM_CODE','REPORT_DATE'], axis=1, inplace=True)
        data['YEAR'] = data['START_DATE'].apply(lambda x: pd.to_datetime(x).year)
        data.drop(['START_DATE'], axis=1, inplace=True)
        pd.set_option('display.float_format', '{:.2f}'.format) 
        data['AMOUNT'] = data['AMOUNT'].apply(lambda x: float(x)//1000000)

        item_order = {item: idx for idx, item in enumerate(data['STD_ITEM_NAME'].unique())}

        pivot_df = data.pivot_table(
            index='STD_ITEM_NAME',
            columns='YEAR',
            values='AMOUNT',
            aggfunc='sum'
        ).reset_index()

        pivot_df.columns.name = None
        pivot_df['original_order'] = pivot_df['STD_ITEM_NAME'].map(item_order)
        pivot_df = pivot_df.sort_values('original_order').drop(columns='original_order')

        year_cols = sorted([col for col in pivot_df.columns if col != 'STD_ITEM_NAME'])
        pivot_df = pivot_df[['STD_ITEM_NAME'] + year_cols]

        pivot_df['nan_count'] = pivot_df.iloc[:, 1:].isna().sum(axis=1)
        filtered_df = pivot_df[pivot_df['nan_count'] <= 3].copy()
        filtered_df.drop(columns='nan_count', inplace=True)

        filtered_df.reset_index(drop=True, inplace=True)

        filtered_df = filtered_df.rename(columns={'STD_ITEM_NAME': '会计年度 (人民币百万)'})
        use_columns = ['会计年度 (人民币百万)'] + [col for col in filtered_df.columns if col != '会计年度 (人民币百万)'][-5:]
        filtered_df = filtered_df.loc[:, use_columns]
        filtered_df['会计年度 (人民币百万)'] = filtered_df['会计年度 (人民币百万)'].apply(lambda x: f"**{x}**" if x.startswith('总') else x)
        return filtered_df
        

    async def api_function(self, stock_code: str, market: str = "HK", period: str = "年度"):
        """
        Fetch the income statement for the requested ticker.
        """
        period = "年度"
        try:
            if market == "HK":
                data = ak.stock_financial_hk_report_em(stock=stock_code, symbol="利润表", indicator=period)
                try:
                    data = self._preprocess_data(data)
                except Exception as e:
                    print("Failed to preprocess income-statement data", e)
            elif market == "A":
                data = ak.stock_financial_benefit_ths(symbol=stock_code, indicator='按年度')
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK' or 'A'.")
        except Exception as e:
            print("Failed to fetch income statement", e)
            print("Parameters", stock_code, market, period)
            data = None
        
        return [
            ToolResult(
                name = f"{self.name} (ticker: {stock_code})",
                description = f"Income statement for ticker {stock_code}.",
                data = data,
                source=f"iFinD/10jqka financials: income statement for {stock_code}. https://basic.10jqka.com.cn/new/{stock_code}/finance.html."
            )
        ]


class CashFlowStatement(Tool):
    def __init__(self):
        super().__init__(
            name="Cash-flow statement",
            description="Returns cash-flow statements showing operating, investing, and financing cash movements for a given ticker.",
            parameters=[
                {"name": "stock_code", "type": "str", "description": "Ticker, e.g., 000001", "required": True},
                {"name": "market", "type": "str", "description": "Market flag: HK or A", "required": True},
            ],
        )

    def prepare_params(self, task) -> dict:
        """
        Build parameters from the routing task.
        """
        if task.stock_code is None:
            # Should already be populated by the router
            assert False, "Stock code cannot be empty"
        else:
            return {"stock_code": task.stock_code, "market": task.market, "period": "年度"}
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the raw cash-flow dataframe into a cleaner pivot table.
        """
        data.drop(['SECUCODE','SECURITY_CODE','SECURITY_NAME_ABBR','ORG_CODE', 'DATE_TYPE_CODE', 'FISCAL_YEAR','STD_ITEM_CODE','REPORT_DATE'], axis=1, inplace=True)
        data['YEAR'] = data['START_DATE'].apply(lambda x: pd.to_datetime(x).year)
        data.drop(['START_DATE'], axis=1, inplace=True)
        pd.set_option('display.float_format', '{:.2f}'.format) 
        data['AMOUNT'] = data['AMOUNT'].apply(lambda x: float(x)//1000000)

        item_order = {item: idx for idx, item in enumerate(data['STD_ITEM_NAME'].unique())}

        pivot_df = data.pivot_table(
            index='STD_ITEM_NAME',
            columns='YEAR',
            values='AMOUNT',
            aggfunc='sum'
        ).reset_index()

        pivot_df.columns.name = None
        pivot_df['original_order'] = pivot_df['STD_ITEM_NAME'].map(item_order)
        pivot_df = pivot_df.sort_values('original_order').drop(columns='original_order')

        year_cols = sorted([col for col in pivot_df.columns if col != 'STD_ITEM_NAME'])
        pivot_df = pivot_df[['STD_ITEM_NAME'] + year_cols]

        pivot_df['nan_count'] = pivot_df.iloc[:, 1:].isna().sum(axis=1)
        filtered_df = pivot_df[pivot_df['nan_count'] <= 3].copy()
        filtered_df.drop(columns='nan_count', inplace=True)

        filtered_df.reset_index(drop=True, inplace=True)

        filtered_df = filtered_df.rename(columns={'STD_ITEM_NAME': '会计年度 (人民币百万)'})
        use_columns = ['会计年度 (人民币百万)'] + [col for col in filtered_df.columns if col != '会计年度 (人民币百万)'][-5:]
        filtered_df = filtered_df.loc[:, use_columns]
        filtered_df['会计年度 (人民币百万)'] = filtered_df['会计年度 (人民币百万)'].apply(lambda x: f"**{x}**" if x.startswith('总') else x)
        return filtered_df


    async def api_function(self, stock_code: str, market: str = "HK", period: str = "年度"):
        """
        Fetch the cash-flow statement for the requested ticker.
        """
        period = "年度"
        try:
            if market == "HK":
                data = ak.stock_financial_hk_report_em(stock=stock_code, symbol="现金流量表", indicator=period)
                try:
                    data = self._preprocess_data(data)
                except Exception as e:
                    print("Failed to preprocess cash-flow data", e)
            elif market == "A":
                #data = ak.stock_cash_flow_sheet_by_yearly_em(symbol=stock_code)
                data = ak.stock_financial_cash_ths(symbol=stock_code, indicator='按年度')
            else:
                raise ValueError(f"Unsupported market flag: {market}. Use 'HK' or 'A'.")
        except Exception as e:
            print("Failed to fetch cash-flow statement", e)
            data = None
        return [
            ToolResult(
                name = f"{self.name} (ticker: {stock_code})",
                description = f"Cash-flow statement for ticker {stock_code}.",
                data = data,
                source=f"iFinD/10jqka financials: cash-flow statement for {stock_code}. https://basic.10jqka.com.cn/new/{stock_code}/finance.html."
            )
        ]
