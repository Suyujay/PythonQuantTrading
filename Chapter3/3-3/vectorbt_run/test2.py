import vectorbt as vbt
import pandas as pd
import numpy as np

# 模擬秒K數據
dates = pd.date_range(start='2025-04-03', periods=100000, freq='1s')
price = pd.Series(np.random.normal(100, 1, 100000), index=dates)

# 指標與信號
fast_ma = vbt.MA.run(price, window=10)
slow_ma = vbt.MA.run(price, window=50)
entries = fast_ma.ma_crossed_above(slow_ma.ma)
exits = fast_ma.ma_crossed_below(slow_ma.ma)

# 回測
portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=10000, freq='1s')
print(portfolio.stats())