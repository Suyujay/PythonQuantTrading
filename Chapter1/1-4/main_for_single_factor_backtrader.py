"""
如果還沒有安裝 backtrader 套件，先在終端機執行「pip install backtrader」
如果還沒有安裝 pyfolio 套件，先在終端機執行「pip install pyfolio-reloaded」
"""

# %%
# 載入需要的套件
import os
import sys

import backtrader as bt
import pandas as pd
import pyfolio as pf

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)


import Chapter1.utils as chap1_utils  # noqa: E402

chap1_utils.finlab_login()

# %%
analysis_period_start_date = "2017-05-16"
analysis_period_end_date = "2021-05-15"

# %%
top_N_stocks = chap1_utils.get_top_stocks_by_market_value(
    excluded_industry=[
        "金融業",
        "金融保險業",
        "存託憑證",
        "建材營造",
    ],
    pre_list_date="2017-01-03",
)


# %%
# 取得指定股票代碼列表在給定日期範圍內的每日 OHLCV 數據。
all_stock_data = chap1_utils.get_daily_OHLCV_data(
    stock_symbols=top_N_stocks,
    start_date=analysis_period_start_date,
    end_date=analysis_period_end_date,
)
all_stock_data["datetime"] = all_stock_data["datetime"].astype(str)
all_stock_data["asset"] = all_stock_data["asset"].astype(str)


# %%
# 指定各個季度下要使用來排序的因子。
# name 對應的是每個季度的因子名稱，
# corr 對應的是因子值與未來收益的關係(根據單因子Alphalens分析結果)。
select_rank_factor_dict = {
    "2017-Q1": {"name": "稅後淨利成長率", "corr": True},
    "2017-Q2": {"name": "稅後淨利成長率", "corr": True},
    "2017-Q3": {"name": "稅後淨利成長率", "corr": True},
    "2017-Q4": {"name": "稅後淨利成長率", "corr": True},
    "2018-Q1": {"name": "稅前淨利成長率", "corr": True},
    "2018-Q2": {"name": "稅前淨利成長率", "corr": True},
    "2018-Q3": {"name": "稅前淨利成長率", "corr": True},
    "2018-Q4": {"name": "稅前淨利成長率", "corr": True},
    "2019-Q1": {"name": "稅後淨利成長率", "corr": True},
    "2019-Q2": {"name": "稅後淨利成長率", "corr": True},
    "2019-Q3": {"name": "稅後淨利成長率", "corr": True},
    "2019-Q4": {"name": "稅後淨利成長率", "corr": True},
    "2020-Q1": {"name": "稅前淨利成長率", "corr": True},
    "2020-Q2": {"name": "稅前淨利成長率", "corr": True},
    "2020-Q3": {"name": "稅前淨利成長率", "corr": True},
    "2020-Q4": {"name": "稅前淨利成長率", "corr": True},
}


# %%
# 準備因子數據，將各季度的因子數據進行排序。
all_factor_data = pd.DataFrame()
for quarter, factor in select_rank_factor_dict.items():
    # 將季度字串轉換為起始和結束日期
    start_date, end_date = chap1_utils.convert_quarter_to_dates(quarter)
    # 生成該季度的交易日範圍
    trading_days = pd.date_range(start=start_date, end=end_date)
    # 取得因子數據，並按股票代碼和日期進行排序與填補
    quarter_factor_data = (
        chap1_utils.get_factor_data(
            stock_symbols=top_N_stocks,
            factor_name=factor["name"],
            trading_days=list(trading_days),
        )
        .reset_index()
        .assign(factor_name=factor["name"])
        .sort_values(by=["asset", "datetime"])
        .groupby("asset", group_keys=False)
        .apply(lambda group: group.ffill())
        .dropna()
    )
    # 根據因子值進行股票排序: 由小到大(positive_corr=True) or 由大到小(positive_corr=False)
    quarter_factor_data = chap1_utils.rank_stocks_by_factor(
        factor_df=quarter_factor_data,
        positive_corr=factor["corr"],  # 根據因子相關性決定排序方向
        rank_column="value",  # 用來排序的欄位名稱
        rank_result_column="rank",  # 儲存排序結果的欄位名稱
    ).drop(columns=["value"])
    # 合併該季度的因子數據
    all_factor_data = pd.concat([all_factor_data, quarter_factor_data])
# 重設索引並將日期與股票代碼轉換為字串格式
all_factor_data = all_factor_data.reset_index(drop=True)
all_factor_data["datetime"] = all_factor_data["datetime"].astype(str)
all_factor_data["asset"] = all_factor_data["asset"].astype(str)

# %%
# 將因子數據與股價數據進行合併
all_stock_and_factor_data = pd.merge(
    all_stock_data, all_factor_data, on=["datetime", "asset"], how="outer"
)
# 按股票代碼和日期排序，並填補遺失值
all_stock_and_factor_data = (
    all_stock_and_factor_data.sort_values(by=["asset", "datetime"])
    .groupby("asset", group_keys=False)
    .apply(lambda group: group.ffill())
    .reset_index(drop=True)
)


# %%
# 定義回測資料格式，新增排名資料
class PandasDataWithRank(bt.feeds.PandasData):
    params = (
        ("datetime", "datetime"),  # 日期欄位
        ("open", "Open"),  # 開盤價欄位
        ("high", "High"),  # 最高價欄位
        ("low", "Low"),  # 最低價欄位
        ("close", "Close"),  # 收盤價欄位
        ("volume", "Volume"),  # 成交量欄位
        ("rank", "rank"),  # 排名欄位
        ("openinterest", -1),  # 持倉量欄位（不使用）
    )
    # 新增因子排名這條數據線
    lines = ("rank",)


# %%
# 定義策略：根據因子排名買入和賣出股票
class FactorRankStrategy(bt.Strategy):
    # 策略參數：要買入和賣出的股票數量，及每檔股票的交易金額
    params = (
        ("buy_n", None),  # 需要買入的股票數量
        ("sell_n", None),  # 需要賣出的股票數量
        ("each_cash", None),  # 每檔股票交易的金額
    )

    def __init__(self):
        self.stocks = self.datas  # 將所有股票數據儲存在 self.stocks 變數中
        self.buy_positions = set()  # 記錄已買入的股票名稱
        self.sell_positions = set()  # 記錄已賣出的股票名稱

    def next(self):
        # 取得當天所有股票的因子排名: ex: {stock1: 1, stock2: 2}
        ranks = {data._name: data.rank[0] for data in self.stocks}
        # 根據排名從低到高排序: 排名越小的因子值越小, 排名越大的因子值越大
        sorted_ranks = sorted(ranks.items(), key=lambda x: x[1])

        # 取得排名最高的 buy_n 個股票（要買入的股票）
        if self.params.buy_n:
            buy_n_list = sorted_ranks[-self.params.buy_n :]
            buy_n_names = [name for name, rank in buy_n_list]  # 提取股票名稱

        # 取得排名最低的 sell_n 個股票（要賣出的股票）
        if self.params.sell_n:
            sell_n_list = sorted_ranks[: self.params.sell_n]
            sell_n_names = [name for name, rank in sell_n_list]  # 提取股票名稱

        # 進行買入與賣出操作
        for data in self.stocks:
            # 取得當前股票名稱
            name = data._name
            # 取得當前股票的收盤價
            close_price = data.close[0]
            # 計算每檔股票的交易股數
            size = int(self.params.each_cash / close_price)
            # 1. 處理賣出(做空)操作
            if self.params.sell_n:
                if name in self.sell_positions and name not in sell_n_names:
                    # 如果股票已賣出且不再賣出清單，則平倉
                    self.close(data)
                    self.sell_positions.remove(name)
                elif name not in self.sell_positions and name in sell_n_names:
                    # 如果股票在賣出清單中，則賣出
                    self.sell(data, size=size)
                    self.sell_positions.add(name)

            # 2. 處理買入(做多)操作
            if self.params.buy_n:
                if name in self.buy_positions and name not in buy_n_names:
                    # 如果股票已買入且不再買入清單，則平倉
                    self.close(data)
                    self.buy_positions.remove(name)
                elif name not in self.buy_positions and name in buy_n_names:
                    # 如果股票在買入清單中，則買入
                    self.buy(data, size=size)
                    self.buy_positions.add(name)


# %%
# 設定回測引擎
cerebro = bt.Cerebro()
# 加入交易策略 FactorRankStrategy，設定策略參數：
# buy_n: 每次要買入的股票數量（20檔）
# sell_n: 每次要賣出的股票數量（20檔）
# each_cash: 每檔股票的交易金額，這裡是總資金的90%除以40檔股票，確保每檔股票有足夠資金配置
cerebro.addstrategy(
    FactorRankStrategy, buy_n=20, sell_n=20, each_cash=2000_0000 * 0.9 / 40
)
# 依序加入每檔股票的數據到回測引擎中
stock_list = list(set(all_stock_and_factor_data["asset"]))
for stock in stock_list:
    data = all_stock_and_factor_data[all_stock_and_factor_data["asset"] == stock]
    data = data.drop(columns=["asset", "factor_name"])  # 移除不必要欄位
    data["datetime"] = pd.to_datetime(data["datetime"])  # 日期欄位轉為 datetime 格式
    data = data.dropna().sort_values(by=["datetime"]).reset_index(drop=True)
    data = PandasDataWithRank(dataname=data)  # 使用自訂的數據格式 PandasDataWithRank
    cerebro.adddata(data, name=stock)  # 加入數據到回測引擎
# 設定初始資金為 2000 萬元
cerebro.broker.set_cash(2000_0000)
# 設定每筆交易的手續費為 0.1%
cerebro.broker.setcommission(commission=0.001)
# 加入 PyFolio 分析器，用於生成投資組合的性能分析報告
cerebro.addanalyzer(bt.analyzers.PyFolio)
# 運行策略
results = cerebro.run()

# %%
# 取得策略結果並生成投資組合分析報告
strat = results[0]  # 取得回測結果中的第一個策略
pyfoliozer = strat.analyzers.getbyname("pyfolio")
(
    returns,
    positions,
    transactions,
    gross_lev,
) = pyfoliozer.get_pf_items()
# 使用 PyFolio 生成完整的投資組合表現分析報告
pf.create_full_tear_sheet(returns)

# %%