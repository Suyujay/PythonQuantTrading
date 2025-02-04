"""
如果還沒有安裝 backtrader 套件，先在終端機執行「pip install backtrader」
如果還沒有安裝 pyfolio 套件，先在終端機執行「pip install pyfolio」
如果還沒有安裝 yfinance 套件，先在終端機執行「pip install yfinance」
"""

# %%
# 載入需要的套件
import backtrader as bt
import pyfolio as pf
import yfinance as yf

# %%
# 分析台積電股票的歷史價格數據，生成投資收益報表
# 取得從 2015/1/1 ~ 2023-12-31 的台積電股票數據
stock_data = yf.download("2330.TW", start="2015-01-01", end="2023-12-31").droplevel(
    "Ticker", axis=1
)
# # 將股票數據的索引（日期）設置為台北時間
# stock_data.index = stock_data.index.tz_localize("Asia/Taipei")
# 計算每日收盤價的百分比變動，這代表每日的收益率
pct_change_close_data = stock_data["Close"].pct_change()
# 使用 PyFolio 生成投資收益報表，分析每日收益率
pf.create_returns_tear_sheet(pct_change_close_data)


# %%
# 將台積電的表現與追蹤大盤指數的 ETF 作比較，生成投資收益報表
# 取得 0050 ETF 從 2015/1/1 ~ 2023-12-31 的數據
benchmark_data = yf.download("0050.TW", start="2015-01-01", end="2023-12-31").droplevel(
    "Ticker", axis=1
)
# # 將股票數據的索引（日期）設置為台北時間
# benchmark_data.index = benchmark_data.index.tz_localize("Asia/Taipei")
# 計算每日收盤價的百分比變動，這代表每日的收益率
pct_change_benchmark_close_data = benchmark_data["Close"].pct_change()
# 使用 PyFolio 生成投資收益報表，將台積電績效表現與 ETF 比較
pf.create_returns_tear_sheet(
    pct_change_close_data, benchmark_rets=pct_change_benchmark_close_data
)


# %%
# 定義每月定期定額策略
class MonthlyInvestmentStrategy(bt.Strategy):
    params = (
        ("cash_to_invest", None),
        ("investment_day", None),
    )

    def __init__(self):
        self.add_timer(
            when=bt.Timer.SESSION_START,
            monthdays=[self.params.investment_day],
        )
        self.order = None

    def notify_timer(self, timer, when, *args, **kwargs):
        """定時器觸發時執行的操作"""
        cash_available = self.broker.getcash()
        price = self.data.close[0]
        size = min(self.params.cash_to_invest, cash_available) // price
        if size > 0:
            self.order = self.buy(size=size)

    def next(self):
        pass


cerebro = bt.Cerebro()  # 初始化回測引擎
# 加載 0050 ETF 的數據（2015/1/1 ~ 2023-12-31）
data = bt.feeds.PandasData(
    dataname=yf.download("0050.TW", "2015-01-01", "2023-12-31").droplevel(
        "Ticker", axis=1
    )
)
cerebro.adddata(data)  # 將數據添加到回測引擎中
# 加載每月定期定額策略，每月投資 10000 元，投資日為每月的第一個交易日
cerebro.addstrategy(MonthlyInvestmentStrategy, cash_to_invest=10000, investment_day=1)
cerebro.broker.setcash(9 * 12 * 10000)  # 設定初始資金
cerebro.broker.setcommission(commission=0.0015)  # 設定交易手續費為
# 添加 PyFolio 分析器，用於在回測後進行分析
cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")
results = cerebro.run()  # 執行回測
strat = results[0]  # 取得第一個策略的結果
# 從策略中取得 PyFolio 分析器，用來進行投資組合績效分析
pyfoliozer = strat.analyzers.getbyname("pyfolio")
# 取得回測結果的四個主要部分，用來進一步分析投資組合的表現
# returns: 投資組合的收益率數據序列（例如每日收益率）
# positions: 投資組合在不同時間點的持倉情況（例如每個時間點持有多少股票）
# transactions: 投資組合的交易紀錄，詳細記錄買入和賣出的每筆交易
# gross_lev: 投資組合的總杠桿率
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
# 使用 PyFolio 生成完整的投資報告，涵蓋收益、持倉、交易等方面的分析
pf.create_full_tear_sheet(returns, positions, transactions)

# %%
