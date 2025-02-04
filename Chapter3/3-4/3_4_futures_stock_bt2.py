#%%
import backtrader as bt
import pandas as pd
import calendar
from datetime import datetime
import empyrical as ep
import pyfolio as pf
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

# 定義期權到期日的計算函數
def option_expiration(date):
    day = 21 - (calendar.weekday(date.year, date.month, 1) + 4) % 7
    return datetime(date.year, date.month, day)

# 定義回測策略
class SampleStrategy(bt.Strategy):
    def log(self, txt, dt=None, is_stock=True):
        # 根據是否為股票或期貨選擇不同的 datetime
        if is_stock:
            dt = dt or self.datas[0].datetime.datetime(0)  # 使用 0050 的 datetime
        else:
            dt = dt or self.datas[1].datetime.datetime(0)  # 使用 TXF 的 datetime
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 保存 0050 和 TXF 的資料
        self.dataclose_0050 = self.datas[0].close
        self.dataclose_txf = self.datas[1].close
        self.order_0050 = None
        self.order_txf = None
        self.first_trade_done = False
        self.cash_reserved_for_txf = 1000000

        # 用來追蹤 0050 的最高獲利
        self.highest_profit = 0
        self.stop_loss_triggered = False

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            is_stock = order.data._name == '0050'
            if order.isbuy():
                self.log(f'''買入執行{order.data._name}, 
                         價格: {order.executed.price:.2f}, 
                         成本: {order.executed.value:.2f}, 
                         手續費 {order.executed.comm:.2f}''', 
                         is_stock=is_stock)
            else:
                self.log(f'''賣出執行{order.data._name}, 
                         價格: {order.executed.price:.2f}, 
                         成本: {order.executed.value:.2f}, 
                         手續費 {order.executed.comm:.2f}''', is_stock=is_stock)
            self.order_0050 = None
            self.order_txf = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        is_stock = trade.data._name == '0050'
        self.log(f'操作利潤{trade.data._name},  淨利 {trade.pnl:.2f}', is_stock=is_stock)

    def next(self):
        position_size = self.getposition(data=self.datas[1]).size 
        futures_date = self.datas[1].datetime.datetime(0)

        # 合約到期日檢查
        if option_expiration(futures_date).day == futures_date.day and futures_date.hour >= 13:
            if position_size != 0:
                self.close(data=self.datas[1])
                self.log('因到期日平倉 TXF 持倉', is_stock=False)
            return  # 不再執行後續邏輯

        # 第一次交易：購買 0050 股票
        if not self.first_trade_done:
            available_cash_for_0050 = self.broker.getcash() - self.cash_reserved_for_txf
            size_0050 = int(available_cash_for_0050 / self.dataclose_0050[0])
            self.order_0050 = self.buy(data=self.datas[0], size=size_0050)
            self.log(f'創建 0050 買入訂單, 大小: {size_0050}', is_stock=True)
            self.first_trade_done = True
            return

        # 計算 0050 的持倉盈虧
        position_0050 = self.getposition(data=self.datas[0])
        current_profit = position_0050.size * (self.dataclose_0050[0] - position_0050.price)

        # 更新最高獲利
        if current_profit > self.highest_profit:
            self.highest_profit = current_profit

        # 獲利回撤 10% 時觸發做空 TXF
        if not self.stop_loss_triggered and current_profit < self.highest_profit * 0.9:
            self.log(f'0050 獲利回撤超過 10%, 創建 TXF 賣出訂單', is_stock=False)
            self.order_txf = self.sell(data=self.datas[1], size=2)  # 賣出 2 口 TXF
            self.stop_loss_triggered = True  

        # 當價格恢復時（0050 盈利重新超過之前的 90%），平倉 TXF
        if self.stop_loss_triggered and current_profit >= self.highest_profit * 0.9:
            self.log(f'0050 盈利回升, 平倉 TXF',is_stock=False)
            self.close(data=self.datas[1])
            self.stop_loss_triggered = False 

# 初始化 cerebro
cerebro = bt.Cerebro()
# 使用 yfinance 加載 0050 的日 K 資料
data_0050 = yf.download('0050.TW', start='2019-03-04', end='2020-02-28').droplevel(
                "Ticker", axis=1
            )
data_0050 = data_0050[['Open', 'High', 'Low', 'Close', 'Volume']]
data_0050 = data_0050.reset_index()
data_0050['Date'] = pd.to_datetime(data_0050['Date'])
# 準備 0050 數據 feed
data_feed_0050 = bt.feeds.PandasData(
    dataname=data_0050,
    name='0050',
    datetime=0,
    high=2,
    low=3,
    open=1,
    close=4,
    volume=5,
    plot=False,
)
cerebro.adddata(data_feed_0050, name='0050')
cerebro.broker.setcommission(commission=0.001, name='0050')

# 加載 TXF 的 30 分鐘 K 線資料
df = pd.read_csv('TXF_30.csv')
df = df.dropna()
df['Date'] = pd.to_datetime(df['Date'])
df.index = df['Date']
df = df.between_time('08:45', '13:45')

# 準備 TXF 數據 feed
data_feed_txf = bt.feeds.PandasData(
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
cerebro.adddata(data_feed_txf, name='TXF')
# 設置初始現金及手續費信息
cerebro.broker.setcash(600000.0)
cerebro.broker.setcommission(commission=200, margin=354000, mult=200,name='TXF')
# 添加策略至 cerebro
cerebro.broker.setcash(5000000.0)
cerebro.addstrategy(SampleStrategy)
# 輸出初始組合資產價值
print('初始組合資產價值: %.2f' % cerebro.broker.getvalue())

# 添加 PyFolio 分析器
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

# 執行回測
results = cerebro.run()

# 輸出最終組合資產價值
print('最終組合資產價值: %.2f' % cerebro.broker.getvalue())

# 使用 PyFolio 分析結果
strat = results[0]
pyfoliozer = strat.analyzers.getbyname('pyfolio')
returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

# 加入 benchmark (0050 的收盤價作為基準)

benchmark_returns = data_0050.set_index('Date')['Close'].pct_change().dropna()
benchmark_returns.index = pd.to_datetime(benchmark_returns.index).tz_localize('UTC')
pf.create_returns_tear_sheet(returns, benchmark_rets=benchmark_returns, positions=positions)
print('累積回報:', ep.cum_returns_final(returns))
print('最大回撤:', ep.max_drawdown(returns))
print('夏普比率:', ep.sharpe_ratio(returns))
# %%
