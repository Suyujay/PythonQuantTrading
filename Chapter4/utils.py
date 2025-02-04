import matplotlib.pyplot as plt
import pandas as pd
import torch
import yfinance as yf
from torch.utils.data import Dataset
from typing_extensions import Annotated


def generate_ticker_data(
    ticker: Annotated[str, "股票代碼"],
    start_date: Annotated[str, "資料開始日期（格式：YYYY-MM-DD）"],
    end_date: Annotated[str, "資料結束日期（格式：YYYY-MM-DD）"],
) -> Annotated[pd.DataFrame, "處理後的股票資料，包含新增的預測收盤價和漲跌方向欄位"]:
    """
    下載股票資料並進行資料預處理。

    步驟:
    1. 下載股票資料，填補遺失值（使用前一日的數值填補）。
    2. 新增欄位 Pred_Close：下一天的收盤價。
    3. 新增欄位 Pred_UpDown：下一天收盤價的上漲或下跌方向（上漲: 1, 下跌: 0）。
    """
    ticker_data = (
        pd.DataFrame(yf.download(ticker, start=start_date, end=end_date))
        .droplevel("Ticker", axis=1)
        .reset_index()
        .ffill()
    )
    ticker_data.columns.name = None

    # 新增 Pred_Close 欄位，表示隔日的收盤價
    ticker_data["Pred_Close"] = ticker_data["Close"].shift(-1)

    # 計算隔日收盤價的變化百分比，並新增欄位
    ticker_data["Pred_PctChange_Close"] = (
        ticker_data["Pred_Close"] - ticker_data["Close"]
    ) / ticker_data["Close"]

    # 根據變化百分比判斷漲跌方向，1 表示上漲，0 表示下跌
    ticker_data["Pred_UpDown"] = ticker_data["Pred_PctChange_Close"].apply(
        lambda x: 1 if x > 0 else 0
    )
    ticker_data = ticker_data.reset_index(drop=True)
    ticker_data = ticker_data.ffill().dropna()
    return ticker_data


def lineplot_true_and_predicted_result(
    true_values: Annotated[pd.Series, "真實的目標值"],
    predicted_values: Annotated[pd.Series, "模型預測的目標值"],
    title: Annotated[str, "圖表標題"],
):
    """
    繪製真實值和預測值的折線圖
    """
    plt.figure(figsize=(14, 7))  # 設定圖表大小
    plt.plot(true_values, label="True", linewidth=3)  # 繪製真實值的折線圖
    plt.plot(predicted_values, label="Predicted", linewidth=3)  # 繪製預測值的折線圖
    plt.title(title, fontsize=30)  # 設定圖表標題及字體大小
    plt.xlabel("Time", fontsize=30)  # 設定X軸標題及字體大小
    plt.ylabel("Close Price", fontsize=30)  # 設定Y軸標題及字體大小
    plt.xticks(fontsize=30)  # 設定X軸刻度字體大小
    plt.yticks(fontsize=30)  # 設定Y軸刻度字體大小
    plt.legend(fontsize=25)  # 設定圖例及字體大小
    plt.show()  # 顯示圖表


class StockDataset(Dataset):
    def __init__(self, data, seq_length, x_idx, y_idx):
        """
        初始化自定義數據集，將資料處理為模型的輸入格式。

        參數:
        - data: 傳入的數據（可以是 numpy array 或 pandas DataFrame）。
        - seq_length: 每個樣本的時間序列長度，即需要過去幾天的數據來預測下一天。
        - x_idx: 特徵欄位的索引（選擇哪些欄位作為模型的輸入）。
        - y_idx: 目標值的索引（選擇哪一欄位作為模型的預測目標）。
        """
        self.data = data  # 儲存傳入的資料
        self.seq_length = seq_length  # 設定每個樣本的時間序列長度
        self.x_idx = x_idx  # 特徵欄位的索引
        self.y_idx = y_idx  # 目標值欄位的索引

    def __len__(self):
        """
        回傳數據集中樣本的總數。
        """
        return self.data.shape[0] - self.seq_length

    def __getitem__(self, idx):
        """
        根據索引回傳一個樣本及其對應的目標值。

        參數:
        - idx: 樣本的起始索引。
        """
        # 取得特徵數據 x
        x = self.data[idx : (idx + self.seq_length), self.x_idx]  # noqa: E203
        x = torch.tensor(x, dtype=torch.float32)
        # 取得目標值 y
        y = self.data[idx + self.seq_length, self.y_idx]
        y = torch.tensor(y, dtype=torch.float32)
        return x, y
