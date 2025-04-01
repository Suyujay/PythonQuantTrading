#%%
import datetime  
import backtrader as bt
import pandas as pd
import calendar
from datetime import datetime 
import empyrical as ep
import pyfolio as pf
import warnings
warnings.filterwarnings('ignore')

def option_expiration(date): 
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 4) % 7 
    return datetime(date.year, date.month, day) 

class MA_Volume_Strategy(bt.Strategy):
    params = (
        ('ma_short', 5),
        ('ma_medium', 30),
        ('ma_long', 40),
        ('vol_ma_short', 5),
        ('vol_ma_long', 40),
        ('stop_loss_pct',   0.00001),  
        ('take_profit_pct', 0.00003), 
    )

    def log(self, txt, dt=None):
        ''' 日誌記錄函數 '''
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 收盤價
        self.dataclose = self.datas[0].close

        # 成交量
        self.datavolume = self.datas[0].volume

        # 移動平均線
        self.ma_short = bt.indicators.SMA(self.dataclose, period=self.params.ma_short)
        self.ma_medium = bt.indicators.SMA(self.dataclose, period=self.params.ma_medium)
        self.ma_long = bt.indicators.SMA(self.dataclose, period=self.params.ma_long)

        # 成交量移動平均線
        self.vol_ma_short = bt.indicators.SMA(self.datavolume, period=self.params.vol_ma_short)
        self.vol_ma_long = bt.indicators.SMA(self.datavolume, period=self.params.vol_ma_long)

        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'''BUY EXECUTED, Price: {order.executed.price:.2f}, 
                         Cost: {order.executed.value:.2f}, 
                         Comm {order.executed.comm:.2f}''')
                self.buycomm = order.executed.comm
            else:
                self.sellprice = order.executed.price
                self.log(f'''SELL EXECUTED, Price: {order.executed.price:.2f},
                          Cost: {order.executed.value:.2f}, 
                          Comm {order.executed.comm:.2f}''')
            self.bar_executed = len(self)
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        if self.order:
            return

        position_size = self.getposition().size
        position_price = self.getposition().price

        status = None
        if (
            option_expiration(self.datas[0].datetime.datetime(0)).day
            == self.datas[0].datetime.datetime(0).day
        ):
            if self.datas[0].datetime.datetime(0).hour >= 13:
                status = "end"
                if  position_size != 0:
                    self.close()
                    self.log("Expired and Create Close Order")

        if status != 'end':
            if not position_size:
                # 多頭進場條件
                if (self.dataclose[0] > self.ma_short[0] and
                    self.dataclose[0] > self.ma_medium[0] and
                    self.dataclose[0] > self.ma_long[0] and
                    self.vol_ma_short[0] > self.vol_ma_long[0]):
                    self.order = self.buy()
                    self.log('創建買單')
                # 空頭進場條件
                elif (self.dataclose[0] < self.ma_short[0] and
                    self.dataclose[0] < self.ma_medium[0] and
                    self.dataclose[0] < self.ma_long[0] and
                    self.vol_ma_short[0] > self.vol_ma_long[0]):
                    self.order = self.sell()
                    self.log('創建賣單')
            else:
                # 已有持倉，檢查出場條件
                if position_size > 0:
                    stop_loss_price = position_price * (1 - self.params.stop_loss_pct)
                    take_profit_price = position_price * (1 + self.params.take_profit_pct)
                    # 多頭持倉
                    if self.dataclose[0] >= take_profit_price:
                        self.order = self.close()
                        self.log('平多單 - 停利')
                    elif self.dataclose[0] <= stop_loss_price:
                        self.order = self.close()
                        self.log('平多單 - 停損')

                elif position_size < 0:
                    stop_loss_price = position_price * (1 + self.params.stop_loss_pct)
                    take_profit_price = position_price * (1 - self.params.take_profit_pct)
                    # 空頭持倉
                    if self.dataclose[0] <= take_profit_price:
                        self.order = self.close()
                        self.log('平空單 - 停利')
                    elif self.dataclose[0] >= stop_loss_price:
                        self.order = self.close()
                        self.log('平空單 - 停損')

# 初始化 Cerebro 引擎
cerebro = bt.Cerebro()
# df = pd.read_csv('TXF_30.csv')
df = pd.read_csv('NQ2503_1min_resampled.csv')
df = df.rename(columns={
    'ds': 'Date',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
})
df = df.dropna()
df['Date'] = pd.to_datetime(df['Date'])
# date_col = 'Date'
# df[date_col] = pd.to_datetime(df[date_col], utc=True)
# df[date_col] = df[date_col].dt.tz_convert('America/New_York')
# df[date_col] = df[date_col].dt.tz_localize(None)
df.index = df['Date']
df = df.between_time('09:20', '10:00')
data_feed = bt.feeds.PandasData(
    dataname=df,
    name='TXF',
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=5,
    plot=True,
)
cerebro.adddata(data_feed, name='TXF')

# 添加策略
cerebro.addstrategy(MA_Volume_Strategy)

# 設定初始資金和交易成本
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=2.2, margin=30000, mult=20)

print('初始資產價值: %.2f' % cerebro.broker.getvalue())
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')

# 執行回測
results = cerebro.run()

print('最終資產價值: %.2f' % cerebro.broker.getvalue())

# 獲取回測結果
strat = results[0]
pyfoliozer = strat.analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

# 生成回測報告
fig = pf.create_returns_tear_sheet(returns, positions=positions, return_fig=True)

# 保存到文件
fig.savefig('strategy_report.png', bbox_inches='tight')

print('累積收益:', ep.cum_returns_final(returns))
print('最大回撤:', ep.max_drawdown(returns))
print('夏普比率:', ep.sharpe_ratio(returns))

trade_analyzer = results[0].analyzers.trade_analyzer.get_analysis()
total_trades = trade_analyzer.total.closed  # 總交易數
won_trades = trade_analyzer.won.total      # 贏利交易數
win_rate = (won_trades / total_trades) * 100 if total_trades > 0 else 0
print(f"總交易數: {total_trades}")
print(f"贏利交易數: {won_trades}")
print(f"勝率: {win_rate:.2f}%")
# %%
cerebro.plot(style='candlestick')