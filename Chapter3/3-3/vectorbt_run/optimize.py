import pandas as pd
from strategy.ma_volume_strategy import MAVolumeStrategy

# 讀取數據
df = pd.read_csv(r'../NQ2503_1min_resampled.csv')
df['Date'] = pd.to_datetime(df['ds'])
df.set_index('Date', inplace=True)


# 創建策略實例
strategy = MAVolumeStrategy()

# 執行回測
portfolio = strategy.optimize(df)