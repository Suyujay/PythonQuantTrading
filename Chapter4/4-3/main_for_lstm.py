# %%
# 載入需要的套件
import json
import os
import random
import sys

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

utils_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(utils_folder_path)

import Chapter4.utils as chap4_utils  # noqa: E402

# %%
# 設置 Python、NumPy 和 PyTorch 的隨機種子, 以確保隨機操作的可重現性。
seed = 1326
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)

# %%
""" 設置數據集時間範圍和訓練超參數 """
# 從 train_config.json 中讀取配置，包括 TICKER、日期範圍和超參數
with open(
    utils_folder_path + "/Chapter4/4-3/train_config.json", "r", encoding="utf-8"
) as file:
    train_config = json.load(file)


# 設定要訓練的股票代碼
TICKER = train_config["TICKER"]

# 設定訓練、驗證、測試資料的開始和結束日期
TRAIN_START_DATE = train_config["TRAIN_START_DATE"]
TRAIN_END_DATE = train_config["TRAIN_END_DATE"]
VALID_START_DATE = train_config["VALID_START_DATE"]
VALID_END_DATE = train_config["VALID_END_DATE"]
TEST_START_DATE = train_config["TEST_START_DATE"]
TEST_END_DATE = train_config["TEST_END_DATE"]

# 設定訓練時相關參數
SEQ_LENGTH = train_config["SEQ_LENGTH"]  # 訓練時使用的序列長度
BATCH_SIZE = train_config["BATCH_SIZE"]  # 訓練時使用的批次大小
LEARNING_RATE = train_config["LEARNING_RATE"]  # 訓練時學習率
EPOCHS = train_config["EPOCHS"]  # 訓練的次數

# 設置 TensorBoard 記錄文件的路徑
WRITER_PATH = utils_folder_path + "/Chapter4/4-3/writer/lstm/"
# 設置模型參數保存的路徑
MODELPARAM_PATH = utils_folder_path + "/Chapter4/4-3/model_param/lstm/"

# %%
""" 數據準備 """
# 生成訓練、驗證和測試數據
train_data = chap4_utils.generate_ticker_data(
    ticker=TICKER,
    start_date=TRAIN_START_DATE,
    end_date=TRAIN_END_DATE,
)[["Open", "High", "Low", "Close", "Volume"]]


valid_data = chap4_utils.generate_ticker_data(
    ticker=TICKER,
    start_date=VALID_START_DATE,
    end_date=VALID_END_DATE,
)[["Open", "High", "Low", "Close", "Volume"]]


test_data = chap4_utils.generate_ticker_data(
    ticker=TICKER, start_date=TEST_START_DATE, end_date=TEST_END_DATE
)[["Open", "High", "Low", "Close", "Volume"]]


# 顯示訓練、驗證和測試集的資料筆數
print(f"訓練集資料筆數: {train_data.shape[0]}")  # 訓練集資料筆數: 488
print(f"測試集資料筆數: {valid_data.shape[0]}")  # 測試集資料筆數: 246
print(f"驗證集資料筆數: {test_data.shape[0]}")  # 驗證集資料筆數: 239

# 進行特徵縮放，使用 MinMaxScaler 將特徵數據縮放到 [0, 1] 範圍內
features_scaler = MinMaxScaler()
# 使用訓練資料擬合縮放器，計算每個特徵的最小值和最大值
# 這一步是根據訓練資料計算縮放標準，並記錄下這些標準
features_scaler.fit(train_data)
# 使用之前計算出的標準，將訓練資料縮放到 [0, 1] 的範圍
train_data = features_scaler.transform(train_data)
# 使用與訓練資料使用相同的縮放規則對驗證資料進行縮放
valid_data = features_scaler.transform(valid_data)
# 使用與訓練資料使用相同的縮放規則對測試資料進行縮放
test_data = features_scaler.transform(test_data)


# 創建訓練、驗證和測試數據集以及對應的數據加載器
train_dataset = chap4_utils.StockDataset(
    train_data,
    SEQ_LENGTH,
    x_idx=[0, 1, 2, 3, 4],  # 特徵索引
    y_idx=3,  # 預測目標為 Close 價格
)
valid_dataset = chap4_utils.StockDataset(
    valid_data,
    SEQ_LENGTH,
    x_idx=[0, 1, 2, 3, 4],
    y_idx=3,
)
test_dataset = chap4_utils.StockDataset(
    test_data,
    SEQ_LENGTH,
    x_idx=[0, 1, 2, 3, 4],
    y_idx=3,
)
# 建立數據加載器，batch_size 決定每次使用多少數據更新
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
valid_loader = DataLoader(valid_dataset, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

# %%
""" 模型定義 """
# 定義 LSTM 模型，用於時間序列預測


class Model(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(Model, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.linear = nn.Linear(in_features=hidden_size, out_features=output_size)

    def forward(self, inputs):
        # (batch_size, seq_length, features_nums) -> (batch_size, seq_length, hidden_size)
        outputs, _ = self.lstm(inputs)

        # 取序列的最後一個時間步長的輸出
        # (batch_size, seq_length, hidden_size) -> (batch_size, hidden_size)
        outputs = outputs[:, -1, :]

        # (batch_size, output_size) -> (batch_size, output_size)
        outputs = self.linear(outputs)
        return outputs


# 創建模型實例
model = Model(input_size=5, hidden_size=64, num_layers=2, output_size=1)

# 設定損失函數，這裡使用 MSE（均方誤差）
loss_fn = nn.MSELoss()

# 設定 Adam 優化器來訓練模型
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

# 創建 TensorBoard 的 SummaryWriter 寫入器，記錄訓練過程
writer = SummaryWriter(WRITER_PATH)
# 記錄超參數設定
hparams = {
    "learning_rate": LEARNING_RATE,
    "batch_size": BATCH_SIZE,
    "sequence_length": SEQ_LENGTH,
    "hidden_size": 64,
    "num_layers": 2,
    "epochs": EPOCHS,
}

# %%
""" 訓練循環 """
print("Start Training")
for epoch in range(EPOCHS):  # 迭代每一個訓練週期
    model.train()  # 將模型設置為訓練模式
    train_loss = 0.0  # 初始化訓練損失為0
    for batch_data in train_loader:  # 迭代每一個訓練批次資料
        inputs, targets = batch_data  # 將批次資料分成特徵和目標
        outputs = model(inputs)  # 透過模型進行前向傳播，獲取預測結果

        # 計算損失值，將模型輸出的預測結果與真實目標進行比較
        loss = loss_fn(outputs, targets.unsqueeze(-1))

        optimizer.zero_grad()  # 將梯度緩衝器歸零，以便計算新的梯度
        loss.backward()  # 執行反向傳播計算梯度
        optimizer.step()  # 更新模型的參數

        train_loss += loss.item()  # 將每個批次的損失值累加起來

    train_loss = train_loss / len(train_loader)  # 計算平均訓練損失
    print(f"Epoch {epoch+1}: Train Loss: {train_loss:.4f}")  # 輸出本輪訓練資料的損失值
    writer.add_scalar(
        tag="Train Loss", scalar_value=train_loss, global_step=epoch
    )  # 將訓練損失值寫入 TensorBoard

    model.eval()  # 將模型設置為評估模式
    val_loss = 0.0  # 初始化驗證損失為0
    with torch.no_grad():  # 停用梯度計算，進行驗證不需要更新參數
        for batch_data in valid_loader:  # 迭代每一個驗證批次資料
            inputs, targets = batch_data  # 將批次資料分成輸入和目標
            outputs = model(inputs)  # 透過模型進行前向傳播，獲取預測結果
            loss = loss_fn(outputs, targets.unsqueeze(-1))  # 計算驗證損失
            val_loss += loss.item()  # 累加驗證損失

    val_loss = val_loss / len(valid_loader.dataset)  # 計算平均驗證損失
    print(f"Epoch {epoch+1}: Valid Loss: {val_loss:.4f}")  # 輸出本輪驗證資料的損失值
    writer.add_scalar(
        tag="Valid Loss", scalar_value=val_loss, global_step=epoch
    )  # 將驗證損失值寫入 TensorBoard

    model.eval()  # 確保模型處於評估模式
    test_loss = 0.0  # 初始化測試損失為0
    with torch.no_grad():  # 停用梯度計算，進行測試不需要更新參數
        for batch_data in test_loader:  # 迭代每一個測試批次資料
            inputs, targets = batch_data  # 將批次資料分成輸入和目標
            outputs = model(inputs)  # 透過模型進行前向傳播，獲取預測結果
            loss = loss_fn(outputs, targets.unsqueeze(-1))  # 計算測試損失
            test_loss += loss.item()  # 累加測試損失

    test_loss = test_loss / len(test_loader.dataset)  # 計算平均測試損失
    print(f"Epoch {epoch}: Test Loss: {test_loss:.4f}")  # 輸出本輪測試資料的損失值
    writer.add_scalar(
        tag="Test Loss", scalar_value=test_loss, global_step=epoch
    )  # 將測試損失值寫入 TensorBoard

    # 每隔 10 個 epoch 保存一次模型參數
    if epoch % 10 == 0 and epoch != 0:
        torch.save(
            model.state_dict(), MODELPARAM_PATH + f"epoch_{epoch+1}.pth"
        )  # 儲存模型

# 最後記錄訓練、驗證和測試損失值
final_metrics = {
    "Train Loss": train_loss,
    "Valid Loss": val_loss,
    "Test Loss": test_loss,
}
writer.add_hparams(hparam_dict=hparams, metric_dict=final_metrics, global_step=epoch)
writer.close()

# %%
""" 繪製訓練集預測結果 """
# 設置模型為評估模式
model.eval()

# 用來儲存訓練集的預測結果和真實值
train_predicted_outputs = []
train_true_outputs = []

# 在不計算梯度下進行推論
with torch.no_grad():
    # 迭代訓練數據加載器中的每個批次數據
    for batch_data in train_loader:
        # 將批次資料分成特徵和目標
        inputs, targets = batch_data
        # 使用模型對輸入進行推論，得到預測結果
        outputs = model(inputs)
        train_predicted_outputs.extend(outputs.squeeze().detach().numpy())  # 預測值
        train_true_outputs.extend(targets.numpy())  # 真實值

# 繪製訓練集的真實值與預測值對比圖
chap4_utils.lineplot_true_and_predicted_result(
    true_values=train_true_outputs,
    predicted_values=train_predicted_outputs,
    title="TRAIN RESULT",
)

# %%
""" 繪製驗證集預測結果 """
model.eval()
valid_predicted_outputs = []
valid_true_outputs = []

with torch.no_grad():
    for batch_data in valid_loader:
        inputs, targets = batch_data
        outputs = model(inputs)
        valid_predicted_outputs.extend(outputs.squeeze().detach().numpy())
        valid_true_outputs.extend(targets.numpy())

chap4_utils.lineplot_true_and_predicted_result(
    true_values=valid_true_outputs,
    predicted_values=valid_predicted_outputs,
    title="VALID RESULT",
)

# %%
""" 繪製測試集預測結果 """
model.eval()
test_predicted_outputs = []
test_true_outputs = []

with torch.no_grad():
    for batch_data in test_loader:
        inputs, targets = batch_data
        outputs = model(inputs)
        test_predicted_outputs.extend(outputs.squeeze().detach().numpy())
        test_true_outputs.extend(targets.numpy())

chap4_utils.lineplot_true_and_predicted_result(
    true_values=test_true_outputs,
    predicted_values=test_predicted_outputs,
    title="TEST RESULT",
)

# %%
