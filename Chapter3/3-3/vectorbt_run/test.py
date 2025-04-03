import vectorbt as vbt
import pandas as pd
import yfinance as yf

# 1. 下載期貨數據
# data = yf.download("CL=F", start="2023-01-01", end="2025-04-03")
data = pd.read_csv(r'../NQ2503_1s_resampled.csv')
data['ds'] = pd.to_datetime(data['ds'])
data.set_index('ds', inplace=True)
price = data['close']  # 單列收盤價
volume = data['volume']

# 定義交易時段
start_time = '09:20:00'
end_time = '10:00:00'
time_mask = (price.index.time >= pd.to_datetime(start_time).time()) & \
            (price.index.time <= pd.to_datetime(end_time).time())

# 2. 計算技術指標
fast_ma = vbt.MA.run(price, window=10)
slow_ma = vbt.MA.run(price, window=50)
volume_ma = vbt.MA.run(volume, window=20)

# 3. 定義進場和出場信號
entries = fast_ma.ma_crossed_above(slow_ma.ma) & time_mask
exits = fast_ma.ma_crossed_below(slow_ma.ma) & time_mask

# 4. 對齊數據（確保索引一致）
# price, entries = price.align(entries, join='inner')
# price, exits = price.align(exits, join='inner')

# 5. 執行回測
portfolio = vbt.Portfolio.from_signals(
    price,
    entries=entries,
    exits=exits,
    init_cash=100000,
    size=20,
    # fees=2.2,
    freq='1s'
)

# 6. 查看結果
print(portfolio.stats())
print(portfolio.wrapper.columns)  # 查看 portfolio 的列名
# portfolio.plot().show()