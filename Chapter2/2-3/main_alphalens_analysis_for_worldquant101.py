# %%
# 載入需要的套件
import os
import sys

import alphalens
import pandas as pd
from tqdm import tqdm

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

import Chapter1.utils as chap1_utils  # noqa: E402
import Chapter2.utils.Alpha_code_1 as Alpha_code_1  # noqa: E402

chap1_utils.finlab_login()

# %%
analysis_period_start_date = "2016-01-01"
analysis_period_end_date = "2019-12-31"

# %%
# 排除指定產業（金融業、金融保險業、存託憑證、建材營造）的股票，
# 並排除上市日期晚於 2012-01-01 的股票，最後篩選市值前 300 大的股票代碼列表。
top_N_stocks = chap1_utils.get_top_stocks_by_market_value(
    pre_list_date="2015-01-05",
)

# %%
# 取得指定股票代碼列表在給定日期範圍內的每日 OHLCV 資料。
all_stock_data = chap1_utils.get_daily_OHLCV_data(
    stock_symbols=top_N_stocks,
    start_date=analysis_period_start_date,
    end_date=analysis_period_end_date,
)

all_stocks_list = []
error_stocks_list = []
alphas_data_dict = {}
# 逐一處理每支股票
for stock in tqdm(top_N_stocks, desc="Processing stocks"):
    try:
        # 取得單支股票 OHLCV 資料
        data = all_stock_data[all_stock_data["asset"] == stock]
        data = data.rename(
            columns={
                "Open": "S_DQ_OPEN",
                "High": "S_DQ_HIGH",
                "Low": "S_DQ_LOW",
                "Close": "S_DQ_CLOSE",
                "Volume": "S_DQ_VOLUME",
            }
        )
        # 使用 Alpha_code_1 模組中的 get_alpha 函數來生成 Alpha 因子
        alphas_data_dict[stock] = Alpha_code_1.get_alpha(data)
        all_stocks_list.append(stock)
    except:
        error_stocks_list.append(stock)

# %%
# 將每支股票的 Alpha 因子結果合併成一個大的 DataFrame
all_alphas_data = pd.DataFrame()
for stock, df in alphas_data_dict.items():
    all_alphas_data = pd.concat([all_alphas_data, df], ignore_index=True)


# %%
# 開始篩選因子：
# 條件一：保留遺失值比例小於 10% 的因子
missing_ratios = all_alphas_data.isnull().mean()
keeping_columns = missing_ratios[missing_ratios < 0.1].index
# 條件二：保留 0 值比例小於 10% 的因子
zero_ratios = (all_alphas_data == 0).mean()
keeping_columns = [col for col in keeping_columns if zero_ratios[col] < 0.1]
# 條件三：只保留浮點數型別的因子
keeping_columns = [
    col for col in keeping_columns if pd.api.types.is_float_dtype(all_alphas_data[col])
]
keeping_columns += ["datetime", "asset"]
all_alphas_data = all_alphas_data[keeping_columns]
print(f"剩下 {len(keeping_columns) - 2} 個因子")

# %%
# 獲取指定股票代碼列表在給定日期範圍內的每日收盤價資料。
close_price_data = chap1_utils.get_daily_close_prices_data(
    stock_symbols=top_N_stocks,
    start_date=analysis_period_start_date,
    end_date=analysis_period_end_date,
)
# 儲存所有 alpha 因子欄位名稱
all_alphas = [
    item
    for item in all_alphas_data.columns
    if item
    not in [
        "S_DQ_OPEN",
        "S_DQ_HIGH",
        "S_DQ_LOW",
        "S_DQ_CLOSE",
        "S_DQ_PCTCHANGE",
        "S_DQ_AMOUNT",
    ]
]

# %%
# 使用 Alphalens 進行因子分析。
alphas_method_list = []
for alphas_method in all_alphas:
    try:
        alphas_data = all_alphas_data[["datetime", "asset", alphas_method]]
        alphas_data = alphas_data.set_index(["datetime", "asset"])
        alphalens_factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
            factor=alphas_data,
            prices=close_price_data,
            periods=(1,),
        )
        print(f"alphas_method: {alphas_method}")
        alphalens.tears.create_returns_tear_sheet(alphalens_factor_data)
        alphas_method_list.append(alphas_method)
    except:
        pass
