import backtrader as bt
import yfinance as yf
import pandas as pd

# 定義策略
class SMACrossStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )

    def __init__(self):
        self.fast_sma = bt.indicators.SMA(self.data.close, period=self.params.fast_period)
        self.slow_sma = bt.indicators.SMA(self.data.close, period=self.params.slow_period)

    def next(self):
        if not self.position:  # 沒有持倉
            if self.fast_sma[0] > self.slow_sma[0]:  # 快速 SMA 上穿慢速 SMA
                self.buy()
        elif self.fast_sma[0] < self.slow_sma[0]:  # 快速 SMA 下穿慢速 SMA
            self.sell()

# 下載數據
# data = yf.download('AAPL', start='2020-01-01', end='2023-01-01',auto_adjust=False)
# data.to_csv('AAPL_data.csv')
data = pd.read_csv('AAPL_data.csv', parse_dates=True, index_col='Date')
print(data.head())


# 設置 Backtrader
cerebro = bt.Cerebro()
cerebro.addstrategy(SMACrossStrategy)
cerebro.broker.setcash(10000.0)

# 將數據轉為 Backtrader 格式
data_feed = bt.feeds.PandasData(
    dataname=data,
    name='TXF',
    # datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    plot=True,
)
cerebro.adddata(data_feed)

# 運行回測
print("Backtrader 開始資金: %.2f" % cerebro.broker.getvalue())
cerebro.run()
print("Backtrader 最終資金: %.2f" % cerebro.broker.getvalue())
backtrader_profit = cerebro.broker.getvalue() - 10000
print("Backtrader 總利潤: %.2f" % backtrader_profit)
cerebro.plot(style='candlestick', iplot=True)