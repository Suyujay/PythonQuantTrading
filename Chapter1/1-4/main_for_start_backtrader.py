"""
如果還沒有安裝 backtrader 套件，先在終端機執行「pip install backtrader」
如果還沒有安裝 yfinance 套件，先在終端機執行「pip install yfinance」
"""

# %%
# 載入需要的套件
import os

import backtrader as bt
import numpy as np
import pandas as pd
import yfinance as yf

# 取得當前檔案的所在目錄: BookCodeV1 的上層目錄 + /BookCodeV1/Chapter1/1-4/
current_dir = os.path.dirname(os.path.abspath(__name__))
parent_dir1 = os.path.abspath(os.path.join(current_dir, ".."))

# %%
"""加載回測數據：讀取 CSV 檔案"""
# 使用 GenericCSVData 方法載入 CSV 格式的股票數據
data = bt.feeds.GenericCSVData(
    dataname=parent_dir1 + "/data/stock_data_example.csv",  # 指定 CSV 檔案的路徑
    datetime=0,  # 設定 datetime 欄位的位置
    open=1,  # 設定 open 欄位的位置
    high=2,  # 設定 high 欄位的位置
    low=3,  # 設定 low 欄位的位置
    close=4,  # 設定 close 欄位的位置
    volume=5,  # 設定 volume 欄位的位置
    openinterest=-1,  # 設定 open interest 欄位，這裡不使用，設為 -1
    dtformat=("%Y-%m-%d"),  # 指定日期格式
)
cerebro = bt.Cerebro()  # 初始化 Cerebro 引擎
cerebro.adddata(data)  # 將數據添加到 Cerebro 中
results = cerebro.run()  # 執行回測


# %%
"""加載回測數據：從 yfinance 下載資料"""
# 使用 PandasData 方法載入 yfinance 股票數據
data_2330 = bt.feeds.PandasData(
    dataname=yf.download("2330.TW", "2020-01-01", "2020-01-31").droplevel(
        "Ticker", axis=1
    )[
        ["Open", "High", "Low", "Close", "Volume"]
    ]  # 下載 2330.TW 股票在指定日期範圍內的數據
)
data_2317 = bt.feeds.PandasData(
    dataname=yf.download("2317.TW", "2020-01-01", "2020-01-31").droplevel(
        "Ticker", axis=1
    )[
        ["Open", "High", "Low", "Close", "Volume"]
    ]  # 下載 2317.TW 股票在指定日期範圍內的數據
)
cerebro = bt.Cerebro()  # 初始化 Cerebro 引擎
cerebro.adddata(data_2330)  # 將 2330.TW 股票數據添加到 Cerebro 中
cerebro.adddata(data_2317)  # 將 2317.TW 股票數據添加到 Cerebro 中
cerebro.run()  # 執行回測


# %%
"""加載回測數據: 自訂資料格式"""
# 生成一個自訂的資料集，包含日期、價格和自定義因子
data = [
    ["2020-01-02", 74.06, 75.15, 73.80, 75.09, 135480400, 1, 11],
    ["2020-01-03", 74.29, 75.14, 74.12, 74.36, 146322800, 2, 12],
    ["2020-01-06", 73.45, 74.99, 73.19, 74.95, 118387200, 3, 13],
    ["2020-01-07", 74.96, 75.22, 74.37, 74.60, 108872000, 4, 14],
    ["2020-01-08", 74.29, 76.11, 74.29, 75.80, 132079200, 5, 15],
]
data = pd.DataFrame(data)  # 將數據轉換為 DataFrame 格式
data.columns = [  # 設定 DataFrame 的欄位名稱
    "datetime",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "factor1",
    "factor2",
]
data["datetime"] = pd.to_datetime(data["datetime"])  # 將 datetime 欄位轉換為日期格式


# 定義包含自定義因子的 PandasData 類別
class PandasDataWithFactor(bt.feeds.PandasData):
    params = (
        ("datetime", "datetime"),  # 對應 datetime 欄位
        ("open", "Open"),  # 對應 open 欄位
        ("high", "High"),  # 對應 high 欄位
        ("low", "Low"),  # 對應 low 欄位
        ("close", "Close"),  # 對應 close 欄位
        ("volume", "Volume"),  # 對應 volume 欄位
        ("factor1", "factor1"),  # 定義自訂因子 factor1，對應第 6 欄位
        ("factor2", "factor2"),  # 定義自訂因子 factor2，對應第 7 欄位
        ("openinterest", -1),  # 不使用 open interest，設為 -1
    )


data = PandasDataWithFactor(dataname=data)  # 初始化 PandasDataWithFactor
cerebro = bt.Cerebro()  # 初始化 Cerebro 引擎
cerebro.adddata(data)  # 將數據添加到 Cerebro 中
cerebro.run()  # 執行回測


# %%
"""範例策略一：印出交易日當天和前一天的開盤價和收盤價"""


# 定義一個策略類別，印出交易日當天和前一天的開盤價和收盤價
class PrintDataStrategy(bt.Strategy):
    # next 方法會在每個時間點被執行
    def next(self):
        # self.datas[0] 代表第一個數據集（即第一支股票）
        date = self.datas[0].datetime.date(0)  # 取得當前交易日的日期
        close = self.datas[0].close[0]  # 取得當前交易日的收盤價
        open = self.datas[0].open[0]  # 取得當前交易日的開盤價
        # len(self.datas[0]) 對應當前是第幾個交易日
        # 隨著每個交易日的進行，len(self.datas[0]) 會不斷增加
        # 每當 next() 方法被調用時，len(self.datas[0]) 值會加 1
        print(
            f"Day-{len(self.datas[0])}, "
            + f"Date: {date}, "
            + f"Close: {close}, "
            + f"Open: {open}"
        )
        # 檢查數據集中是否有前一天的資料
        # 這個檢查是為了避免存取不存在的前一天資料
        if len(self.datas[0]) > 1:
            # 索引 [-1] 表示前一個時間點的數據
            # 取得前一個交易日的日期、收盤價和開盤價
            yesterday_date = self.datas[0].datetime.date(-1)
            yesterday_close = self.datas[0].close[-1]
            yesterday_open = self.datas[0].open[-1]
            print(
                f"Yesterday Date: {yesterday_date}, "
                + f"Close: {yesterday_close}, "
                + f"Open: {yesterday_open}"
            )
        print("----------------------------------------------------------")


data = bt.feeds.GenericCSVData(
    dataname=parent_dir1 + "/data/stock_data_example.csv",  # 指定 CSV 檔案的路徑
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    openinterest=-1,
    dtformat=("%Y-%m-%d"),
)
cerebro = bt.Cerebro()  # 初始化回測引擎
cerebro.adddata(data)  # 加載數據
cerebro.addstrategy(PrintDataStrategy)  # 加載策略
results = cerebro.run()  # 執行回測


# %%
"""
範例策略二：
當收盤價 < 開盤價（收黑）時買入，
當收盤價 > 開盤價（收紅）時賣出，
當收盤價 = 開盤價時不執行操作。
"""


class OpenCloseStrategy(bt.Strategy):
    def __init__(self):
        self.order = None  # 初始化訂單狀態為 None，訂單狀態會隨著交易變更
        self.close = self.datas[0].close  # 取得第一個數據集的收盤價資料
        self.open = self.datas[0].open  # 取得第一個數據集的開盤價資料

    def log(self, txt, dt=None):
        """記錄策略日誌的函數"""
        # 如果沒有指定日期，則預設為當前交易日日期
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """訂單通知處理"""
        if order.status in [order.Submitted]:
            self.log("訂單已提交")
        if order.status in [order.Accepted]:
            self.log("訂單已接受")
        if order.status in [order.Canceled]:
            self.log("訂單取消")
        if order.status in [order.Margin]:
            self.log("保證金不足")
        if order.status in [order.Rejected]:
            self.log("訂單被拒絕")
        if order.status in [order.Completed]:
            executed_price = np.round(order.executed.price, 3)
            executed_comm = np.round(order.executed.comm, 3)
            if order.isbuy():
                self.log(
                    "訂單完成: 買入執行, "
                    + f"價格: {executed_price}, "
                    + f"手續費 {executed_comm}"
                )
            elif order.issell():
                self.log(
                    "訂單完成: 賣出執行, "
                    + f"價格: {executed_price}, "
                    + f"手續費 {executed_comm}"
                )

    def notify_trade(self, trade):
        """交易通知處理"""
        if trade.isclosed:  # 交易結束時
            trade_pnl = np.round(trade.pnl, 2)
            trade_pnlcomm = np.round(trade.pnlcomm, 2)
            self.log(f"考慮手續費的利潤: {trade_pnlcomm}")
            self.log(f"不考慮手續費的利潤: {trade_pnl}")

    def next(self):
        today_open = np.round(self.open[0], 2)
        today_close = np.round(self.close[0], 2)
        self.log(f"當前收盤價: {today_close}, " + f"當前開盤價: {today_open}")
        if self.close[0] < self.open[0]:
            # 如果收盤價小於開盤價，表示當日收黑，則執行買入操作
            self.buy(size=1)  # 買入一股
            self.log("收盤價小於開盤價, 執行買入")
        elif self.close[0] > self.open[0]:
            # 如果收盤價大於開盤價，表示當日收紅，則執行賣出操作
            self.sell(size=1)  # 賣出一股
            self.log("收盤價大於開盤價, 執行賣出")


# 加載數據
data = bt.feeds.GenericCSVData(
    dataname=parent_dir1 + "/data/stock_data_example.csv",  # 指定 CSV 檔案的路徑
    datetime=0,  # 設定 datetime 欄位的位置
    open=1,  # 設定 open 欄位的位置
    high=2,  # 設定 high 欄位的位置
    low=3,  # 設定 low 欄位的位置
    close=4,  # 設定 close 欄位的位置
    volume=5,  # 設定 volume 欄位的位置
    openinterest=-1,  # 設定 open interest 欄位，這裡不使用，設為 -1
    dtformat=("%Y-%m-%d"),  # 指定日期格式
)
cerebro = bt.Cerebro()  # 初始化回測引擎
cerebro.adddata(data)  # 加載數據
cerebro.addstrategy(OpenCloseStrategy)  # 加載策略
cerebro.broker.setcash(100000)  # 設置初始資金
cerebro.broker.setcommission(commission=0.0015)  # 設置交易手續費
results = cerebro.run()  # 執行回測


# %%
"""範例策略三：每月定期定額0050"""


class MonthlyInvestmentStrategy(bt.Strategy):
    # 定義策略的參數
    params = (
        ("cash_to_invest", None),  # 每月計劃投資的金額
        ("investment_day", None),  # 每月的投資日（哪一天執行定期投資）
    )

    def __init__(self):
        # 初始化一個定時器，設置在每個月的指定投資日執行操作
        self.add_timer(
            when=bt.Timer.SESSION_START,  # 在指定交易日開始時觸發
            monthdays=[self.params.investment_day],  # 每月的指定投資日
        )
        # 初始化訂單狀態為 None，用來追蹤當前的訂單
        self.order = None

    def log(self, txt, dt=None):
        """記錄策略日誌的函數"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """訂單通知處理"""
        if order.status in [order.Completed]:
            # 取得成交價格
            executed_price = np.round(order.executed.price, 2)
            # 取得手續費
            executed_comm = np.round(order.executed.comm, 2)
            self.log(
                "訂單完成: 買入執行, "
                + f"價格: {executed_price}, 手續費 {executed_comm}"
            )

    def notify_timer(self, timer, when, *args, **kwargs):
        """定時器觸發時執行的操作"""
        self.log("定投日, 執行買入訂單")
        # 取得當前帳戶可用的現金金額
        cash_available = self.broker.getcash()
        # 取得當前收盤價
        price = self.data.close[0]
        # 根據每月計劃投資的金額（self.params.cash_to_invest）和可用的現金
        # 計算可以買入的股票數量 size
        size = min(self.params.cash_to_invest, cash_available) // price
        if size > 0:
            # 如果計算出可以買的股票數量大於 0，則執行買入訂單
            self.order = self.buy(size=size)

    # next 是在每個交易日都會被使用的方法，但這個範例中不做任何操作，
    # 全都交由定時器控制交易
    def next(self):
        pass


cerebro = bt.Cerebro()  # 初始化回測引擎
# 加載數據
asset = "0050.TW"
data = bt.feeds.PandasData(
    dataname=yf.download(asset, "2011-01-01", "2020-12-31").droplevel("Ticker", axis=1)[
        ["Open", "High", "Low", "Close", "Volume"]
    ]
)
cerebro.adddata(data)
# 加載策略（每個月投資一萬且交易日設定為每個月第一個交易日）
cerebro.addstrategy(MonthlyInvestmentStrategy, cash_to_invest=10000, investment_day=1)
initial_cash = 10 * 12 * 10000  # 初始資金
cerebro.broker.setcash(initial_cash)
cerebro.broker.setcommission(commission=0.0015)  # 設置交易手續費
# 加載分析器
cerebro.addanalyzer(bt.analyzers.SharpeRatio)
cerebro.addanalyzer(bt.analyzers.DrawDown)
cerebro.addanalyzer(bt.analyzers.Returns)
cerebro.addanalyzer(bt.analyzers.PyFolio)
# 執行回測
results = cerebro.run()
strat = results[0]
# 輸出分析器的分析結果
print("Sharpe Ratio:", strat.analyzers.sharperatio.get_analysis())
print("Drawdown:", strat.analyzers.drawdown.get_analysis())
print("Returns:", strat.analyzers.returns.get_analysis())
# 輸出broker內資訊
print("-------------------------------------------------------")
print(f"股票代碼: {asset}")
positions = cerebro.broker.getposition(data)
print(f"總投資股數: {positions.size}")
final_portfolio_value = cerebro.broker.getvalue()
print(f"總資產(包含剩餘現金): {final_portfolio_value:.2f}")
profit = (final_portfolio_value - initial_cash) / initial_cash
print(f"總收益率: {profit * 100:.2f}%")
final_cash = cerebro.broker.getcash()
print(f"最終現金餘額: {final_cash:.2f}")


# %%
"""範例策略四：移動平均交叉策略"""


class MovingAverageCrossStrategy(bt.Strategy):
    # 定義策略的參數: 短期移動平均線週期和長期移動平均線週期
    params = (("short_period", 5), ("long_period", 20))

    def __init__(self):
        # 5日均線作為短期移動平均線
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period
        )
        # 20日均線作為長期移動平均線
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period
        )
        # 初始化訂單狀態,用來追蹤當前的訂單
        self.order = None

    def next(self):
        if not self.position:  # 當下沒有任何持倉
            # 如果短期移動平均線高於長期移動平均線，則買入股票
            if self.short_sma > self.long_sma:
                self.buy()
        else:  # 當下已經有倉位
            # 如果短期移動平均線低於長期移動平均線，則賣出股票
            if self.short_sma < self.long_sma:
                self.order = self.sell()  # 賣出股票

    def log(self, txt, dt=None):
        """記錄策略日誌的函數"""
        # 如果沒有指定日期，則預設為當前交易日日期
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """訂單通知處理"""
        if order.status in [order.Completed]:
            executed_price = np.round(order.executed.price, 3)
            executed_comm = np.round(order.executed.comm, 3)
            if order.isbuy():
                self.log(
                    "訂單完成: 買入執行, "
                    + f"價格: {executed_price}, "
                    + f"手續費 {executed_comm}"
                )
            elif order.issell():
                self.log(
                    "訂單完成: 賣出執行, "
                    + f"價格: {executed_price}, "
                    + f"手續費 {executed_comm}"
                )


cerebro = bt.Cerebro()
cerebro.addstrategy(MovingAverageCrossStrategy)
asset = "2330.TW"
data = bt.feeds.PandasData(
    dataname=yf.download(asset, "2021-01-01", "2021-12-31").droplevel("Ticker", axis=1)[
        ["Open", "High", "Low", "Close", "Volume"]
    ]
)
cerebro.adddata(data)
cerebro.broker.setcash(1000000)
cerebro.broker.setcommission(commission=0.0015)
cerebro.run()


# %%
"""範例策略五：RSI 過度買入/賣出策略"""


class RSIStrategy(bt.Strategy):
    # 定義策略的參數：rsi_period, rsi_low, rsi_high
    # rsi_period: RSI 的計算週期,預設為14天
    # rsi_low: 當 RSI 低於此數值時進行買入,預設為30
    # rsi_high: 當 RSI 高於此數值時進行賣出,預設為70
    params = (("rsi_period", 14), ("rsi_low", 30), ("rsi_high", 70))
    params = (("rsi_period", 14), ("rsi_low", 30), ("rsi_high", 70))

    def __init__(self):
        # 使用參數中設定的 rsi_period 來計算 RSI
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
        # 初始化訂單狀態,用來追蹤當前的訂單
        self.order = None

    def next(self):
        if not self.position:  # 當下沒有任何持倉
            # 如果 RSI 低於設定的 rsi_low 參數值（預設為30），表示市場超賣，執行買入操作
            if self.rsi < self.params.rsi_low:
                self.buy()
        else:  # 當下已經有倉位
            # 如果 RSI 高於設定的 rsi_high 參數值（預設為70），表示市場超買，執行賣出操作
            if self.rsi > self.params.rsi_high:
                self.sell()

    def log(self, txt, dt=None):
        """記錄策略日誌的函數"""
        # 如果沒有指定日期，則預設為當前交易日日期
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def notify_order(self, order):
        """訂單通知處理"""
        if order.status in [order.Completed]:
            executed_price = np.round(order.executed.price, 3)
            executed_comm = np.round(order.executed.comm, 3)
            if order.isbuy():
                self.log(
                    "訂單完成: 買入執行, "
                    + f"價格: {executed_price}, "
                    + f"手續費 {executed_comm}"
                )
            elif order.issell():
                self.log(
                    "訂單完成: 賣出執行, "
                    + f"價格: {executed_price}, "
                    + f"手續費 {executed_comm}"
                )


cerebro = bt.Cerebro()
cerebro.addstrategy(RSIStrategy)
asset = "0050.TW"
data = bt.feeds.PandasData(
    dataname=yf.download(asset, "2011-01-01", "2020-12-31").droplevel("Ticker", axis=1)[
        ["Open", "High", "Low", "Close", "Volume"]
    ]
)
cerebro.adddata(data)
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(commission=0.0015)
cerebro.run()

# %%
