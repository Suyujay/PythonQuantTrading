#%%
import datetime as dt
import backtrader as bt
import pandas as pd
import calendar
from datetime import datetime 
import empyrical as ep
import pyfolio as pf
import warnings
warnings.filterwarnings('ignore')

# 導入策略模組
from strategy.ma_volume_strategy import MA_Volume_Strategy

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
df = df.between_time('07:50', '10:10')
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