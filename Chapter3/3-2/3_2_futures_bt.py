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


print(option_expiration(datetime.now()))


class SampleStrategy(bt.Strategy):
    params = (
        ('period_day', 5),  
        ('stop_loss', 0.01),  # 1% stop loss
        ('take_profit', 0.01),  # 1% take profit
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.order = None
        self.sellprice = None
        self.buycomm = None

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

        position = self.getposition().size
        status = None
        if (
            option_expiration(self.datas[0].datetime.datetime(0)).day
            == self.datas[0].datetime.datetime(0).day
        ):
            if self.datas[0].datetime.datetime(0).hour >= 13:
                status = "end"
                if  position != 0:
                    self.close()
                    self.log("Expired and Create Close Order")

        if status != 'end':
            if not position:
                if self.dataclose[0] > self.datahigh[-1]:  # Breakout above the high
                    self.buy()
                    self.log('BUY ORDER CREATED')
                elif self.dataclose[0] < self.datalow[-1]:  # Breakout below the low
                    self.sell()
                    self.log('SELL ORDER CREATED')

            # Exit Conditions
            if position > 0 :  # Long position
                if (self.dataclose[0] > self.position.price * (1 + self.params.take_profit) or  # Take profit
                    self.dataclose[0] < self.position.price * (1 - self.params.stop_loss)):  # Stop loss
                    self.close()
                    self.log('CLOSE LONG POSITION')

            elif position < 0:  # Short position
                if (self.dataclose[0] < self.position.price * (1 - self.params.take_profit) or  # Take profit
                    self.dataclose[0] > self.position.price * (1 + self.params.stop_loss)):  # Stop loss
                    self.close()
                    self.log('CLOSE SHORT POSITION')



cerebro = bt.Cerebro()
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
cerebro.addstrategy(SampleStrategy)
cerebro.broker.setcash(300000.0)

cerebro.broker.setcommission(commission=200, margin=167000, mult=200)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

results = cerebro.run()

print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

strat = results[0]
pyfoliozer = strat.analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

pf.create_returns_tear_sheet(returns, positions=positions)
print('cum returns:', ep.cum_returns_final(returns))
print('mdd:', ep.max_drawdown(returns))
print('sharpe:', ep.sharpe_ratio(returns))
# %%
