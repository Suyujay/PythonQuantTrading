"""
1.如果還沒有安裝 TA-Lib 套件，先在終端機執行「pip install TA-Lib」
"""

import pandas as pd

# %%
# 載入需要的套件
import talib
import yfinance as yf
from talib import abstract  # noqa: F401

# %%
# 取得 TALIB 支援的所有技術指標名稱列表
all_ta_indicators = talib.get_functions()
# 列出 TALIB 支援的技術指標總數量
print(f"TALIB 支援的技術指標總數量: {len(all_ta_indicators)}")

# 取得依類別分組後的技術指標名稱列表，例如分成動量指標、Cycle指標等
all_group_ta_indicators = talib.get_function_groups()
# 列出所有技術指標分類的名稱
print(f"TALIB 所有技術指標分類的名稱: {list(all_group_ta_indicators.keys())}")


# %%
# 使用 yfinance 下載台泥（股票代碼 1101.TW）從 2022-01-01 到 2022-12-31 的股市資料
data = (
    pd.DataFrame(yf.download("1101.TW", start="2022-01-01", end="2022-12-31"))
    .droplevel("Ticker", axis=1)
    .reset_index()
    .ffill()
)

# %%
# 方法一：使用標準 TALIB 函數進行技術指標計算
# 計算 30 天的簡單移動平均線（SMA），並將結果存入新的欄位 "SMA"
data["SMA"] = talib.SMA(real=data["Close"], timeperiod=30)

# 計算 14 天的相對強弱指標（RSI），並將結果存入新的欄位 "RSI"
data["RSI"] = talib.RSI(data["Close"], timeperiod=14)

# 查看隨機指標（STOCH）的參數和使用說明
print("STOCH 函數說明：")
help(talib.STOCH)

# 計算隨機指標（STOCH），包括%K線和%D線，並將結果存入對應欄位
# %K 和 %D 是隨機指標的兩條線，快線 (fast %K) 和慢線 (slow %D)
data["STOCH_K"], data["STOCH_D"] = talib.STOCH(
    high=data["High"],
    low=data["Low"],
    close=data["Close"],
    fastk_period=5,  # 快線 %K 的週期為 5
    slowk_period=3,  # 慢線 %K 的週期為 3
    slowk_matype=0,  # 慢線 %K 的移動平均類型為簡單移動平均
    slowd_period=3,  # 慢線 %D 的週期為 3
    slowd_matype=0,  # 慢線 %D 的移動平均類型為簡單移動平均
)

# 計算移動平均收斂發散指標（MACD），包括 MACD 線、訊號線和柱狀圖，並將結果存入對應欄位
data["MACD"], data["MACDSignal"], data["MACDHist"] = talib.MACD(
    data["Close"],
    fastperiod=12,  # 快線的週期為 12
    slowperiod=26,  # 慢線的週期為 26
    signalperiod=9,  # 訊號線的週期為 9
)

# 計算布林帶（Bollinger Bands），包括上軌線、中軌線和下軌線，並將結果存入對應欄位
data["BBANDS_upper"], data["BBANDS_middle"], data["BBANDS_lower"] = talib.BBANDS(
    data["Close"],
    timeperiod=5,  # 布林帶的週期為 5
    nbdevup=2.0,  # 上軌線與中軌線之間的標準差為 2
    nbdevdn=2.0,  # 下軌線與中軌線之間的標準差為 2
    matype=0,  # 移動平均的類型為簡單移動平均
)

# 查看後幾筆資料
print(data.tail())

# %%
# 方法二：使用 TALIB 的 abstract 模組進行技術指標計算
# 使用 abstract 模組時，資料欄位必須符合 TALIB 所需的格式
# TALIB 要求的資料欄位名稱為 "open", "high", "low", "close"

# 重新命名資料欄位名稱，使其符合 TALIB 所需的格式
data = data.rename(
    columns={"Open": "open", "High": "high", "Low": "low", "Close": "close"}
)

# 使用 TALIB 的 abstract 模組計算 30 天的簡單移動平均線（SMA），並將結果存入 "SMA" 欄位
data["SMA"] = talib.abstract.SMA(data, timeperiod=30)

# 使用 TALIB 的 abstract 模組計算 14 天的相對強弱指標（RSI），並將結果存入 "RSI" 欄位
data["RSI"] = talib.abstract.RSI(data, timeperiod=14)

# 查看後幾筆資料
print(data.tail())

# %%
