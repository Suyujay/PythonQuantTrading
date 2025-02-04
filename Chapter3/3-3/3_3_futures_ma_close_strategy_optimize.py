#%%
import datetime  
import backtrader as bt
import pandas as pd
import calendar
from datetime import datetime 
import empyrical as ep
import pyfolio as pf
import itertools
import warnings
warnings.filterwarnings('ignore')

def option_expiration(date): 
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 4) % 7 
    return datetime(date.year, date.month, day) 

class MA_Volume_Strategy(bt.Strategy):
    params = (
        ('ma_short', 5),
        ('ma_medium', 20),
        ('ma_long', 60),
        ('stop_loss_pct', 0.02),  
        ('take_profit_pct', 0.02), 
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
        self.vol_ma_short = bt.indicators.SMA(self.datavolume, period=self.params.ma_short)
        self.vol_ma_long = bt.indicators.SMA(self.datavolume, period=self.params.ma_long)

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
                    self.vol_ma_short[0] < self.vol_ma_long[0]):
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
cerebro = bt.Cerebro(optreturn=False)

df = pd.read_csv('TXF_30.csv')
df = df.dropna()
df['Date'] = pd.to_datetime(df['Date'])
df.index = df['Date']
df = df.between_time('08:45', '13:45')

data_feed = bt.feeds.PandasData(
    dataname=df,
    name='TXF',
    datetime=0,
    high=2,
    low=3,
    open=1,
    close=4,
    volume=5,
    plot=False,
)
cerebro.adddata(data_feed, name='TXF')

# 參數範圍
ma_short_values = [3, 5, 10]
ma_medium_values = [15, 20, 30]
ma_long_values = [40, 60, 90]
stop_loss_values = [0.02, 0.01, 0.03, 0.05]
take_profit_values = [0.02, 0.01, 0.03, 0.05]

# 添加策略的排列組合
cerebro.optstrategy(MA_Volume_Strategy,
                    ma_short=ma_short_values,
                    ma_medium=ma_medium_values,
                    ma_long=ma_long_values,
                    stop_loss_pct=stop_loss_values,
                    take_profit_pct=take_profit_values)

# 設定初始資金和交易成本
cerebro.broker.setcash(300000.0)
cerebro.broker.setcommission(commission=200, margin=167000, mult=200)

# 添加 PyFolio 分析器
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# 執行回測
results = cerebro.run(maxcpus=1)

# 將結果保存為 Excel
output = []
for result in results:
    strat = result[0]
    pyfoliozer = strat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    
    cum_return = ep.cum_returns_final(returns)
    sharpe_ratio = ep.sharpe_ratio(returns)
    mdd = ep.max_drawdown(returns)
    
    output.append({
        'ma_short': strat.params.ma_short,
        'ma_medium': strat.params.ma_medium,
        'ma_long': strat.params.ma_long,
        'stop_loss_pct': strat.params.stop_loss_pct,
        'take_profit_pct': strat.params.take_profit_pct,
        'cum_return': cum_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': mdd
    })

df_output = pd.DataFrame(output)
df_output.to_excel('optimization_results.xlsx', index=False)
print('結果已保存到 optimization_results.xlsx')

# %%
