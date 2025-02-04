"""
1.如果還沒有安裝 xgboost 套件，先在終端機執行「pip install xgboost」
"""

# %%
import os
import sys

import matplotlib.pyplot as plt
import xgboost
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

import Chapter4.utils as chap4_utils  # noqa: E402

# %%
# 使用 0050.TW 在 2020-01-01 至 2021-12-31 的資料當作訓練資料
# 生成訓練和測試所需的資料，資料包含隔日的收盤價漲跌方向
all_data = chap4_utils.generate_ticker_data(
    ticker="0050.TW", start_date="2020-01-01", end_date="2021-12-31"
)
# 取得特徵欄位（開盤價、最高價、最低價、收盤價、交易量）
features_data = all_data[["Open", "High", "Low", "Close", "Volume"]]
# 取得目標欄位（隔日收盤價上漲或是下跌的方向，1 表示上漲，0 表示下跌）
labels_data = all_data["Pred_UpDown"]

# %%
# 將資料分割為訓練集和測試集
# 將前 50% 資料設為訓練集 (X_train, y_train)，後 50% 資料設為測試集 (X_test, y_test)
# X_train：訓練集的特徵，y_train：訓練集的目標
# X_test：測試集的特徵，y_test：測試集的目標
X_train, X_test, y_train, y_test = train_test_split(
    features_data, labels_data, test_size=0.5, random_state=1326, shuffle=False
)

print(f"訓練集資料筆數: {X_train.shape[0]}")  # 訓練集資料筆數: 244
print(f"測試集資料筆數: {X_test.shape[0]}")  # 測試集資料筆數: 244


# %%
# 創建 DMatrix 數據集，這是 XGBoost 專用的數據格式
dtrain = xgboost.DMatrix(X_train, label=y_train)
dtest = xgboost.DMatrix(X_test, label=y_test)

# %%
# 設置 XGBoost 參數
params = {
    "objective": "binary:logistic",  # 設定目標函數為二元邏輯回歸（適合二分類任務）
    "eval_metric": "logloss",  # 評估指標使用 logloss
    "eta": 0.01,  # 設定學習率
    "max_depth": 3,  # 設定樹的最大深度
    "subsample": 0.8,  # 設定子樣本比例，防止過擬合
}

# 建立 XGBoost 模型並進行訓練
# bst 代表訓練後的模型
bst = xgboost.train(
    params=params,  # 設置的模型參數
    dtrain=dtrain,  # 訓練資料
)

# %%
# 使用訓練好的模型來進行預測
# 對訓練集進行預測，取得預測的機率
y_pred_prob = bst.predict(dtrain)
# 將預測機率轉換為預測的類別（大於 0.546 為 1，否則為 0）
y_train_pred = (y_pred_prob > 0.546).astype(int)

# 對測試集進行預測，取得預測的機率
y_pred_prob = bst.predict(dtest)
# 將預測機率轉換為預測的類別（大於 0.545 為 1，否則為 0）
y_test_pred = (y_pred_prob > 0.545).astype(int)


# %%
# 評估模型在訓練集和測試集的表現
# 使用分類報告（precision、recall、f1-score、support、accuracy 等指標）來評估模型

# 生成訓練集的分類報告，評估模型在訓練集上的表現
classification_report_train = classification_report(y_true=y_train, y_pred=y_train_pred)
print("Train Classification Report: ")
print(classification_report_train)

# 生成測試集的分類報告，評估模型在測試集上的表現
classification_report_test = classification_report(y_true=y_test, y_pred=y_test_pred)
print("Test Classification Report: ")
print(classification_report_test)


# %%
# 繪製特徵重要性圖
# 使用 XGBoost 提供的 plot_importance 函數來視覺化呈現每個特徵對模型的影響
xgboost.plot_importance(bst)
plt.show()  # 顯示特徵重要性圖表

# %%
