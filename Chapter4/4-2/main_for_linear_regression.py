# %%
# 載入所需套件
import os
import sys

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

import Chapter4.utils as chap4_utils  # noqa: E402

# %%
# 使用 0050.TW 在 2020-01-01 至 2021-12-31 的資料當作訓練資料
# 生成訓練和測試所需的資料
all_data = chap4_utils.generate_ticker_data(
    ticker="0050.TW", start_date="2020-01-01", end_date="2021-12-31"
)
# 取得特徵欄位（開盤價、最高價、最低價、收盤價、交易量）
features_data = all_data[["Open", "High", "Low", "Close", "Volume"]]
# 取得訓練目標欄位（隔日收盤價）
labels_data = all_data["Pred_Close"]

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
# 建立線性迴歸模型
model = LinearRegression()

# 使用訓練資料來訓練模型
# X_train：訓練集的特徵，y_train：訓練集的目標
model.fit(X_train, y_train)

# 使用訓練好的模型來預測（推論）
# y_train_pred：模型對訓練集的預測結果
y_train_pred = model.predict(X_train)
# y_test_pred：模型對測試集的預測結果
y_test_pred = model.predict(X_test)

# %%
# 使用均方誤差（MSE）來評估模型在訓練集和測試集的表現
# 均方誤差越小表示預測越準確

# 計算訓練集的 MSE
mse_train = mean_squared_error(y_true=y_train, y_pred=y_train_pred)
print(f"Train Mean Squared Error: {mse_train:.2f}")

# 計算測試集的 MSE
mse_test = mean_squared_error(y_true=y_test, y_pred=y_test_pred)
print(f"Test Mean Squared Error: {mse_test:.2f}")


# %%
# 繪製訓練集真實值和預測值的折線圖
chap4_utils.lineplot_true_and_predicted_result(
    true_values=y_train.values,
    predicted_values=y_train_pred,
    title="Linear Regression Result For TrainSet",
)
# 繪製測試集真實值和預測值的折線圖
chap4_utils.lineplot_true_and_predicted_result(
    true_values=y_test.values,
    predicted_values=y_test_pred,
    title="Linear Regression Result For TestSet",
)

# %%
