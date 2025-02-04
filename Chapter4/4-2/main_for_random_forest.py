# %%
# 載入所需套件
import os
import sys

import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
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
# 建立隨機森林模型
model = RandomForestClassifier(n_estimators=10, random_state=1326)

# 使用訓練資料來訓練模型
# X_train：訓練集的特徵，y_train：訓練集的目標
model.fit(X_train, y_train)

# 使用訓練好的模型來預測（推論）
# y_train_pred：模型對訓練集的預測結果
y_train_pred = model.predict(X_train)
# y_test_pred：模型對測試集的預測結果
y_test_pred = model.predict(X_test)

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
# 取得各個變數（特徵）的重要程度
# model.feature_importances_ 回傳每個特徵對模型決策的重要性
importance = model.feature_importances_
feature_names = features_data.columns

# 將變數的重要程度以長條圖表示
plt.figure(figsize=(8, 6))
plt.barh(feature_names, importance)
plt.xlabel("Feature Importance", fontsize=15)
plt.ylabel("Feature", fontsize=15)
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.title("Feature Importance of Random Forest", fontsize=15)
plt.show()

# %%
