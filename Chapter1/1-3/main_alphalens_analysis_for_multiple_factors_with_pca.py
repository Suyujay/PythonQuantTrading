"""
如果還沒有安裝 alphalens 套件，先在終端機執行「pip install alphalens-reloaded」
如果還沒有安裝 scikit-learn 套件，先在終端機執行「pip install -U scikit-learn」
"""

# %%
# 載入需要的套件。
import os
import sys

import numpy as np
import pandas as pd
from alphalens.tears import create_full_tear_sheet
from alphalens.utils import get_clean_factor_and_forward_returns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

import Chapter1.utils as chap1_utils  # noqa: E402

chap1_utils.finlab_login()

# %%
analysis_period_start_date = "2017-05-16"
analysis_period_end_date = "2021-05-15"

# %%
top_N_stocks = chap1_utils.get_top_stocks_by_market_value(
    excluded_industry=[
        "金融業",
        "金融保險業",
        "存託憑證",
        "建材營造",
    ],
    pre_list_date="2017-01-03",
)

# %%
# 獲取指定股票代碼列表在給定日期範圍內的每日收盤價資料。
# 對應到財報資料時間 2017-Q1~2020-Q4
close_price_data = chap1_utils.get_daily_close_prices_data(
    stock_symbols=top_N_stocks,
    start_date=analysis_period_start_date,
    end_date=analysis_period_end_date,
)

# %%
# 要進行主成分分析的因子列表。
all_factors_list = [
    "營業利益",
    "營運現金流",
    "歸屬母公司淨利",
    "經常稅後淨利",
    "ROE稅後",
    "營業利益成長率",
    "稅前淨利成長率",
    "稅後淨利成長率",
    "應收帳款週轉率",
]

# %%
# 取得 FinLab 多個因子資料。
# 將多個因子資料集整合(concat)成一個資料集。
factors_data_dict = {}
for factor in all_factors_list:
    factor_data = (
        chap1_utils.get_factor_data(
            stock_symbols=top_N_stocks,
            factor_name=factor,
            trading_days=list(close_price_data.index),
        )
        .reset_index()
        .assign(factor_name=factor)
    )
    factors_data_dict[factor] = factor_data

# %%
# 將所有因子資料合併成一個 DataFrame
concat_factors_data = pd.concat(factors_data_dict.values(), ignore_index=True)
# 將資料格式轉換為索引是 datetime 和 asset，欄位名稱是因子名稱
concat_factors_data = concat_factors_data.pivot_table(
    index=["datetime", "asset"], columns="factor_name", values="value"
)
# 處理異常值和遺失值，將無窮大的值替換為 NaN，並透過向前填補的方法填補遺失值
concat_factors_data.replace([np.inf, -np.inf], np.nan, inplace=True)
print(concat_factors_data)

# %%
# 進行主成分分析。
# 首先對因子數據進行標準化處理，以保證每個因子的尺度相同。
# 這個標準化過程會將每個因子數據的平均值調整為0, 標準差調整為1。
scaler = StandardScaler()
scale_concat_factors_data = scaler.fit_transform(concat_factors_data.dropna().values)

# %%
# 設置要提取的主成分數量為 8 ，這裡選擇了比財報因子數少一個的主成分數量。
pac_components_num = len(all_factors_list) - 1
print(pac_components_num)
pca = PCA(n_components=pac_components_num)
# 對標準化後的資料進行 PCA 分析。
principal_components = pca.fit_transform(scale_concat_factors_data)

# %%
# 將原始資料轉換成主成分分析結果表。每一行代表一個主成分。
principal_df = pd.DataFrame(
    data=principal_components,
    index=concat_factors_data.dropna().index,
    columns=[f"PC{i}" for i in range(1, pac_components_num + 1)],
)
principal_df

# %%
# 產生主成分係數表
loadings = pd.DataFrame(
    pca.components_,
    columns=concat_factors_data.columns,
    index=[f"PC{i+1}" for i in range(pca.n_components_)],
)
print("主成分係數表, index 是第i個主成分, columns 是第j個財報因子:")
loadings

# %%
# 產生主成分的資訊保留比例表
explained_variance_ratio = pd.DataFrame(
    pca.explained_variance_ratio_,
    index=[f"PC{i+1}" for i in range(pca.n_components_)],
    columns=["可解釋比例"],
)
print("主成分各自可解釋比例:")
explained_variance_ratio

# %%
# 產生主成分的資訊保留累積比例表
cumulative_variance_ratio = pd.DataFrame(
    np.cumsum(pca.explained_variance_ratio_),
    index=[f"使用前{i+1}個主成分" for i in range(pca.n_components_)],
    columns=["累積可解釋比例"],
)
print("累積可解釋比例:")
cumulative_variance_ratio

# %%
# 使用 Alphalens 進行第二主成分的因子分析。
alphalens_factor_data = get_clean_factor_and_forward_returns(
    factor=principal_df[["PC2"]].squeeze(),
    prices=close_price_data,
    quantiles=5,
    periods=(1,),
)
create_full_tear_sheet(alphalens_factor_data)

# %%
# 使用 Alphalens 進行第四主成分的因子分析。
alphalens_factor_data = get_clean_factor_and_forward_returns(
    factor=principal_df[["PC4"]].squeeze(),
    prices=close_price_data,
    quantiles=5,
    periods=(1,),
)
create_full_tear_sheet(alphalens_factor_data)

# %%
