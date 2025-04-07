import pandas as pd
from strategy.ma_volume_strategy import MAVolumeStrategy

# 讀取數據
df = pd.read_csv(r'../NQ2503_1min_resampled.csv')
df['Date'] = pd.to_datetime(df['ds'])
# df = df.rename(columns={
#     'open': 'Open',
#     'high': 'High',
#     'low': 'Low',
#     'close': 'Close',
#     'volume': 'Volume',
# })
df.set_index('Date', inplace=True)


# 創建策略實例
strategy = MAVolumeStrategy()

# 執行回測
portfolio = strategy.backtest(df, initial_capital=100000.0)

# 顯示結果
print(portfolio.stats())
# print(f"總收益: {portfolio.total_return():.2%}")
# print(f"夏普比率: {portfolio.sharpe_ratio():.2f}")
# print(f"最大回撤: {portfolio.max_drawdown():.2%}")
# print(f"勝率: {portfolio.trades.win_rate():.2%}")

# 繪製績效圖表
portfolio.plot().show()