# %%
# 載入需要的套件
import os
import sys

import pandas as pd
import yfinance as yf

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

# 載入 Chapter2/utils/ 資料夾中的 alphas191.py 模組
import Chapter2.utils.alphas as alphas  # noqa: E402
import Chapter2.utils.alphas191 as alphas191  # noqa: E402

# %%
"""
備註:
在計算 Alpha 因子時，許多指標會依賴過去數天的歷史數據，
因此如果只選取所需的日期範圍，可能會導致早期的 Alpha 因子無法正確計算。
為了解決這個問題，建議在選取資料時擴大日期範圍，
這樣可以確保計算 Alpha 因子時有足夠的歷史數據可用。
計算完所有因子後，再篩選出需要分析的時間段資料即可。
"""

# 使用 yfinance 取得台泥 (1101.TW) 股票資料，日期範圍為 2021-11-01 到 2022-12-31
data = (
    pd.DataFrame(yf.download("1101.TW", start="2021-11-01", end="2022-12-31"))
    .droplevel("Ticker", axis=1)
    .reset_index()
    .ffill()
)
data.columns.name = None
# 重新命名資料表的欄位名稱，以符合 Alpha191 模組要求
data = data.rename(
    columns={
        "Close": "close",  # 收盤價
        "Open": "open",  # 開盤價
        "Volume": "volume",  # 交易量
        "Low": "low",  # 最低價
        "High": "high",  # 最高價
    }
)

# %%
# 加入基準資料 (0050.TW) 的資料，用於 Alpha191 模組比較分析
benchmark_data = (
    pd.DataFrame(yf.download("0050.TW", start="2016-01-01", end="2019-12-31"))
    .droplevel("Ticker", axis=1)
    .reset_index()
    .ffill()
)
benchmark_data.columns.name = None
# 將基準資料的開盤價與收盤價加入到 data 中
data["benchmark_open"] = benchmark_data["Open"]
data["benchmark_close"] = benchmark_data["Close"]
# 填補資料中的遺失值
data = data.ffill().dropna()

# %%
# 初始化 Alphas191 類別，並傳入台泥的股票資料
alpha_2330 = alphas191.Alphas191(data)
# 取得所有 Alpha 方法的列表
alpha_methods = alphas.Alphas.get_alpha_methods(alphas191.Alphas191)
alpha_dict = {}  # 儲存成功執行的 Alpha 因子結果
error_method = []  # 儲存執行失敗的 Alpha 方法名稱
success_method = []  # 儲存執行成功的 Alpha 方法名稱

# 逐一執行所有 Alpha 方法，並記錄執行成功或失敗的情況
for method in alpha_methods:
    try:
        # 執行每個 Alpha 方法，並將結果存入 DataFrame
        df = getattr(alpha_2330, method)()
        # 根據產生的欄位數量，為結果設定新欄位名稱
        new_columns = [f"{method}_{i+1}" for i in range(int(df.shape[1]))]
        df.columns = new_columns
        # 將結果儲存到 alpha_dict 中
        alpha_dict[method] = df
        # 將成功的 Alpha 方法名稱加入 success_method 列表
        success_method.append(method)
    except Exception as e:
        # 如果執行失敗，將失敗的 Alpha 方法名稱加入 error_method 列表，並顯示錯誤訊息
        error_method.append(method)
        print(f"Error in method {method}: {e}")

# 計算執行失敗的 Alpha 方法數量
len(error_method)

# 將所有成功執行的 Alpha 方法的結果合併成一個 DataFrame
# 每個 column 代表一個 Alpha 因子
alpha_data = pd.concat(alpha_dict.values(), axis=1)

# %%
# 設定三個條件來篩選 Alpha 因子：

# 條件一：保留遺失值比例小於 10% 的因子
# 計算每個因子遺失值的比例
missing_ratios = alpha_data.isnull().mean()
# 只保留遺失值比例小於 10% 的因子
keeping_columns = missing_ratios[missing_ratios < 0.1].index
print(f"剩下 {len(keeping_columns)} 個因子")

# 條件二：保留 0 值比例小於 10% 的因子
# 計算每個因子中 0 值的比例
zero_ratios = (alpha_data == 0).mean()
# 只保留 0 值比例小於 10% 的因子
keeping_columns = [col for col in keeping_columns if zero_ratios[col] < 0.1]
print(f"剩下 {len(keeping_columns)} 個因子")

# 條件三：只保留浮點數型別的因子
# 檢查每個因子是否為浮點數型別，並只保留是浮點數型別的因子
keeping_columns = [
    col for col in keeping_columns if pd.api.types.is_float_dtype(alpha_data[col])
]
print(f"剩下 {len(keeping_columns)} 個因子")
print(f"剩下的因子名稱: {keeping_columns}")

# %%
# 根據篩選條件保留符合條件的 Alpha 因子
alpha_data = alpha_data[keeping_columns].ffill().dropna()

# %%
# 顯示前幾筆 Alpha 因子資料
alpha_data.head()
