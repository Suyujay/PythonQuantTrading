# %%
# 載入需要的套件
import os
import sys

import pandas as pd
import yfinance as yf

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

# 載入 Chapter2/utils/ 資料夾中的 Alpha_code_1.py 模組
import Chapter2.utils.Alpha_code_1 as Alpha_code_1  # noqa: E402

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
# 重新命名資料表的欄位名稱，以符合使用 Alpha_code_1 模組要求的格式
data = data.rename(
    columns={
        "Open": "S_DQ_OPEN",  # 開盤價
        "High": "S_DQ_HIGH",  # 最高價
        "Low": "S_DQ_LOW",  # 最低價
        "Close": "S_DQ_CLOSE",  # 收盤價
        "Volume": "S_DQ_VOLUME",  # 成交量
    }
)

# %%
# 使用 Alpha_code_1 模組中的 get_alpha 函數生成 Alpha 因子
# alpha_data 的每一個欄位代表一個不同的 Alpha 因子
alpha_data = Alpha_code_1.get_alpha(data)

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
# 檢查每個因子是否為浮點數型別，只保留是浮點數型別的因子
keeping_columns = [
    col for col in keeping_columns if pd.api.types.is_float_dtype(alpha_data[col])
]
print(f"剩下 {len(keeping_columns)} 個因子")
print(f"剩下因子名稱: {keeping_columns}")


# %%
# 根據篩選條件保留符合條件的 Alpha 因子
# 填補缺失值
keeping_columns += ["Date"]
alpha_data = alpha_data[keeping_columns].ffill().dropna()

# %%
# 將資料篩選到指定的日期範圍內，這裡篩選出 2022 年的資料
alpha_data = alpha_data[
    (alpha_data["Date"] >= "2022-01-01") & (alpha_data["Date"] <= "2022-12-31")
].reset_index(drop=True)

# %%
# 顯示前幾筆 Alpha 因子資料
alpha_data.head()

# %%
