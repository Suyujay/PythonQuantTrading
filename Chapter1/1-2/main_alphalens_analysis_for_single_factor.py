"""
如果還沒有安裝 alphalens 套件，先在終端機執行「pip install alphalens-reloaded」
"""

# %%
# 載入需要的套件。
import json
import os
import sys

from alphalens.tears import create_full_tear_sheet
from alphalens.utils import get_clean_factor_and_forward_returns

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)
# 載入 Chapter1 資料夾中的 utils.py 模組，並命名為 chap1_utils
import Chapter1.utils as chap1_utils  # noqa: E402

# 使用 FinLab API token 登入 FinLab 平台，取得資料訪問權限。
chap1_utils.finlab_login()

# %%
analysis_period_start_date = "2017-05-16"
analysis_period_end_date = "2021-05-15"

# %%
"""
Part1. 使用「營業利益」這個因子來做示範
"""

# %%
# 排除指定產業（金融業、金融保險業、存託憑證、建材營造）的股票，
# 並排除上市日期晚於 2017-01-03 的股票。
top_N_stocks = chap1_utils.get_top_stocks_by_market_value(
    excluded_industry=[
        "金融業",
        "金融保險業",
        "存託憑證",
        "建材營造",
    ],
    pre_list_date="2017-01-03",
)

print(f"股票數量: {len(top_N_stocks)}")  # 757

# %%
# 獲取指定股票代碼列表在給定日期範圍內的每日收盤價資料。
# 對應到財報資料時間 2017-Q1~2020-Q4
close_price_data = chap1_utils.get_daily_close_prices_data(
    stock_symbols=top_N_stocks,
    start_date=analysis_period_start_date,
    end_date=analysis_period_end_date,
)
close_price_data.head()
close_price_data.tail()
print(f"股票代碼(欄位名稱): {close_price_data.columns}")
print(f"日期(索引): {close_price_data.index}")

# %%
# 獲取指定因子（營業利益）的資料，並根據每日的交易日將因子資料擴展成日頻資料。
factor_data = chap1_utils.get_factor_data(
    stock_symbols=top_N_stocks,
    factor_name="營業利益",
    trading_days=sorted(list(close_price_data.index)),
)
factor_data = factor_data.dropna()
factor_data.head()
factor_data.tail()
print(f"列出欄位名稱{factor_data.columns}")
print(f"列出索引名稱(日期,股票代碼): {factor_data.index}")
print(f"列出所有日期: {factor_data.index.get_level_values(0)}")
print(f"列出所有股票代碼: {factor_data.index.get_level_values(1)}")

# %%
# Multi-index DataFrame 操作：查看特定日期（2018-05-10）所有股票的因子值。
factor_data.loc[("2018-05-10", slice(None)), :]
# Multi-index DataFrame 操作：查看特定股票（如 2330）的所有日期的因子值。
factor_data.loc[(slice(None), "2330"), :]

# %%
# 使用 Alphalens 將因子數據與收益數據結合，
# 生成 Alphalens 分析所需的數據表格。
alphalens_factor_data = get_clean_factor_and_forward_returns(
    factor=factor_data.squeeze(),
    prices=close_price_data,
    quantiles=5,
)
alphalens_factor_data

# %%
# 使用 Alphalens 生成完整的因子分析圖表報告。
create_full_tear_sheet(alphalens_factor_data)

# %%
"""
Part2.
接下來我們會用 for 迴圈來執行多個因子的分析。
事先將 FinLab 中 fundamental_features 類別下的因子儲存在 factors_list.json 中，
後續可以透過 json.load 把 factors_list.json 內的變數載入環境內重複使用。
"""

# %%
with open(
    utils_folder_path + "/Chapter1/1-2/factors_list.json",
    "r",
    encoding="utf-8",
) as file:
    result = json.load(file)

# 從載入的 JSON 文件中提取因子名稱列表，準備進行分析。
fundamental_features_list = result["fundamental_features"]
print(f"將要分析的因子清單: {fundamental_features_list}")
print(f"總計有 {len(fundamental_features_list)} 個因子")

# %%
# 使用 for 迴圈從 FinLab 獲取多個因子的資料。
# 將所有因子資料儲存到字典 factors_data_dict 中，鍵為因子名稱，值為對應的因子資料。
factors_data_dict = {}
for factor in fundamental_features_list:
    factor_data = chap1_utils.get_factor_data(
        stock_symbols=top_N_stocks,
        factor_name=factor,
        trading_days=list(close_price_data.index),
    )
    factors_data_dict[factor] = factor_data

# %%
# 使用 Alphalens 進行因子分析。
for factor in fundamental_features_list:
    print(f"factor: {factor}")
    alphalens_factor_data = get_clean_factor_and_forward_returns(
        factor=factors_data_dict[factor].squeeze(),
        prices=close_price_data,
        periods=(1,),
    )
    create_full_tear_sheet(alphalens_factor_data)
    print("--------------------------------------------------------------")
