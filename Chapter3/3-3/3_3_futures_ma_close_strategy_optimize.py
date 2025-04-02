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

from strategy.ma_volume_strategy import MA_Volume_Strategy

# 初始化 Cerebro 引擎
cerebro = bt.Cerebro(optreturn=False)

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
df.index = df['Date']
df = df.between_time('07:50', '10:10')

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
stddev_short_values = [3,5,10]
stddev_long_values = [15, 30, 60]
vol_ma_short_values = [3, 5, 10]
# vol_ma_long_values = [15, 20, 30, 40, 60, 90]
vol_ma_short_threshold_values = [1500, 2000]
stop_loss_values = [0.00001, 0.00005]
take_profit_values = [0.00001, 0.00005]

# 添加策略的排列組合
cerebro.optstrategy(MA_Volume_Strategy,
                    ma_short=ma_short_values,
                    ma_medium=ma_medium_values,
                    ma_long=ma_long_values,
                    stddev_short_values=stddev_short_values,
                    stddev_long_values=stddev_long_values,
                    vol_ma_short=vol_ma_short_values,
                    vol_ma_short_threshold=vol_ma_short_threshold_values,
                    stop_loss_pct=stop_loss_values,
                    take_profit_pct=take_profit_values)

# 設定初始資金和交易成本
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=2.2, margin=30000, mult=20)

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
        'stddev_short': strat.params.stddev_short,
        'stddev_long': strat.params.stddev_long,
        'vol_ma_short': strat.params.vol_ma_short,
        'vol_ma_short_threshold': strat.params.vol_ma_short_threshold,
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
