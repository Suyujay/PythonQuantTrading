#%%
import yfinance as yf
import pandas as pd
import pyfolio as pf
# # 使用 yfinance 加載 0050 的日 K 資料
data_0050 = yf.download('0050.TW', start='2019-03-04', end='2020-02-28').droplevel(
                "Ticker", axis=1
            )
print(data_0050)
data_0050 = data_0050[['Open', 'High', 'Low', 'Close', 'Volume']]
data_0050 = data_0050.reset_index()
data_0050['Date'] = pd.to_datetime(data_0050['Date'])

benchmark_returns = data_0050.set_index('Date')['Close'].pct_change().dropna()
benchmark_returns.index = pd.to_datetime(benchmark_returns.index)
print(benchmark_returns)
pf.create_returns_tear_sheet(benchmark_returns)

# %%
