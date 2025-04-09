import vectorbt as vbt
import numpy as np
import pandas as pd

# 1. 加載那斯達克指數期貨數據（這裡以 Yahoo Finance 的 NQ=F 為例）
# data = vbt.YFData.download("NQ=F", start="2025-03-01", end="2025-04-10", interval="5m").get()
data = pd.read_csv(r'Chapter3\3-3\NQ2503_1min_resampled.csv')
data['ds'] = pd.to_datetime(data['ds'])
data.set_index('ds', inplace=True)
price = data["close"]

# 2. 定義市場結構檢測函數（簡化版）
def detect_swing_points(price, window=50):
    # 檢測高點和低點
    highs = price.rolling(window).max()
    lows = price.rolling(window).min()
    is_high = (price == highs).shift(1).fillna(False)
    is_low = (price == lows).shift(1).fillna(False)
    return is_high, is_low

# 3. 實現 ICT 策略邏輯
swing_highs, swing_lows = detect_swing_points(price)

# 流動性抓取：價格突破前高後回撤
breakout_high = price > price[swing_highs].reindex(price.index, method="ffill")
liquidity_grab = breakout_high & (price < price[swing_highs].reindex(price.index, method="ffill")).shift(1)

# OTE：簡單使用 61.8% 回撤作為入場點（這裡簡化為價格回撤至前高低點間的中點）
ote_level = (price[swing_highs].reindex(price.index, method="ffill") + 
             price[swing_lows].reindex(price.index, method="ffill")) * 0.5
entry_condition = liquidity_grab & (price >= ote_level)

# 出場：固定 50 點目標（根據 NQ 期貨的點值調整）
profit_target = 50  # NQ 每點價值為 $0.25，50 點 = $12.5
profit_target_condition = price >= (price[entry_condition].reindex(price.index, method="ffill") + profit_target)
# 加入停損條件：這裡以固定 30 點作為停損（根據實際需求調整）
stop_loss_amount = 10
# 當價格跌破進場價格（使用 entry_condition 對應的參考價格）減去停損點數時，觸發停損
stop_loss_condition = price <= (price[swing_lows].reindex(price.index, method="ffill") - stop_loss_amount)

# 假設 self.trading_start 與 self.trading_end 已定義交易時段
trading_start = pd.to_datetime("09:30").time()
trading_end = pd.to_datetime("10:00").time()
time_mask = ((price.index.time >= trading_start) & (price.index.time < trading_end))
# 當前數據點不屬於交易時段，即使其他條件未滿足也強制出場
exit_on_non_trading = ~time_mask
exit_condition = profit_target_condition | stop_loss_condition | exit_on_non_trading

# 4. 生成交易信號
entries = entry_condition
exits = exit_condition

# 5. 回測
pf = vbt.Portfolio.from_signals(
    price,
    entries,
    exits,
    init_cash=100000,  # 初始資金
    size=1,
    min_size=1,
    # fixed_fees=2.2,
    freq="5m",        # 時間頻率
)

# 6. 輸出結果
# print("總回報:", pf.total_return())
# print("勝率:", pf.trades.win_rate())
# print("最大回撤:", pf.max_drawdown())
print(pf.stats())

# 可視化
pf.plot().show()