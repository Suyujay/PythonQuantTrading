import vectorbt as vbt
import yfinance as yf
import pandas as pd

# 下載數據（與 Backtrader 使用相同數據）
# data = yf.download('AAPL', start='2020-01-01', end='2023-01-01')
data = pd.read_csv('AAPL_data.csv', parse_dates=True, index_col='Date')
price = data['Close']

# 計算快速和慢速 SMA
fast_sma = vbt.MA.run(price, window=10)
slow_sma = vbt.MA.run(price, window=30)

# 生成買賣信號
entries = fast_sma.ma_crossed_above(slow_sma)
exits = fast_sma.ma_crossed_below(slow_sma)

# 運行回測
portfolio = vbt.Portfolio.from_signals(
    close=price,
    entries=entries,
    exits=exits,
    init_cash=10000,
    size=1,
    accumulate=False,
    fees=0.0,  # 設置為 0 以與 Backtrader 保持一致
    freq='1d'  # 設置為日頻率
)

# 輸出結果
print("VectorBT 總利潤: %.2f" % portfolio.total_profit())
# 顯示結果
print(portfolio.stats())

# 繪製績效圖表
portfolio.plot().show()