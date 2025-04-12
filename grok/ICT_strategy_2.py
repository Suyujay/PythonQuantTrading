import datetime as dt
import vectorbt as vbt
import numpy as np
import pandas as pd
from vectorbt.portfolio.enums import SizeType

class ICTStrategy:
    """
    使用 ICT 策略進行那斯達克指數期貨回測

    參數:
        ma_short: 短期移動平均線窗口
        ma_medium: 中期移動平均線窗口
        ma_long: 長期移動平均線窗口
        stddev_short: 短期標準差窗口
        stddev_long: 長期標準差窗口
        vol_ma_short: 成交量移動平均線窗口
        vol_ma_short_threshold: 成交量閾值
        initial_capital: 初始資金
        stop_loss_pct: 止損比例（使用 vectorbt sl_stop 參數）
        take_profit_pct: 停利比例（使用 vectorbt tp_stop 參數）
        trading_start: 交易開始時間
        trading_end: 交易結束時間
    """
    def __init__(
        self,
        ma_short: int = 3,
        ma_medium: int = 20,
        ma_long: int = 120,
        stddev_short: int = 3,
        stddev_long: int = 20,
        vol_ma_short: int = 10,
        vol_ma_short_threshold: float = 2000,
        initial_capital: float = 100000,
        stop_loss_pct: float = 0.0005,
        take_profit_pct: float = 0.0005,
        trading_start: dt.time = dt.time(9, 30),
        trading_end: dt.time = dt.time(10, 0)
    ):
        """
        初始化策略參數
        """
        self.ma_short = ma_short
        self.ma_medium = ma_medium
        self.ma_long = ma_long
        self.stddev_short = stddev_short
        self.stddev_long = stddev_long
        self.vol_ma_short = vol_ma_short
        self.vol_ma_short_threshold = vol_ma_short_threshold
        self.initial_capital = initial_capital
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trading_start = trading_start
        self.trading_end = trading_end

    def detect_swing_points(self, price, window=50):
        """
        簡化版市場高低點檢測（swing points）
        """
        highs = price.rolling(window).max()
        lows = price.rolling(window).min()
        is_high = (price == highs).shift(1).fillna(False)
        is_low = (price == lows).shift(1).fillna(False)
        return is_high, is_low

    def run(self, df: pd.DataFrame) -> vbt.Portfolio:
        """
        執行 ICT 策略回測

        參數:
            df: 需包含 'open', 'high', 'low', 'close' 欄位，且索引必須為 DatetimeIndex
        返回:
            vbt.Portfolio 回測結果
        """
        # 取得收盤價格
        price = df["close"]

        # 1. 檢測市場結構：高點與低點
        swing_highs, swing_lows = self.detect_swing_points(price)

        # 2. 流動性抓取：價格突破前高後回撤
        breakout_high = price > price[swing_highs].reindex(price.index, method="ffill")
        liquidity_grab = breakout_high & (price < price[swing_highs].reindex(price.index, method="ffill")).shift(1)

        # 3. OTE：以前高低點中點作為入場參考
        ote_level = (price[swing_highs].reindex(price.index, method="ffill") + 
                     price[swing_lows].reindex(price.index, method="ffill")) * 0.5
        entry_condition = liquidity_grab & (price >= ote_level)

        # 4. 交易時段控制：只在交易時段內持倉，非交易時段強制平倉
        time_mask = ((price.index.time >= self.trading_start) & (price.index.time < self.trading_end))
        # time_mask = pd.Series(time_mask, index=price.index)
        exit_on_non_trading = ~time_mask
        exit_condition = exit_on_non_trading

        # 5. 進出場信號
        entries = entry_condition
        exits = exit_condition
        

        # 6. 回測：使用 vectorbt 封裝回測邏輯
        portfolio = vbt.Portfolio.from_signals(
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            entries=entries,
            exits=exits,
            size=20,                    # 固定部位數量
            min_size=20,
            size_type=SizeType.Percent,  # 固定下單數量
            init_cash=self.initial_capital,
            fixed_fees=2.2,             # 手續費（範例值）
            sl_stop=self.stop_loss_pct,
            tp_stop=self.take_profit_pct,
            accumulate=False,           # 不累積部位
            freq='1min'
        )
        # portfolio = vbt.Portfolio.from_signals(
        #     close=df['close'],
        #     entries=entries,
        #     exits=exits,
        #     init_cash=100000,  # 初始資金
        #     size=20,
        #     min_size=20,
        #     fixed_fees=2.2,
        #     freq="1m",        # 時間頻率
        # )
        return portfolio

# 使用示例
if __name__ == "__main__":
    # 讀取數據
    df = pd.read_csv(r'Chapter3\3-3\NQ2503_1min_resampled.csv')
    df['ds'] = pd.to_datetime(df['ds'])
    df.set_index('ds', inplace=True)

    # 建立策略實例
    strategy = ICTStrategy(initial_capital=100000, stop_loss_pct=0.0005, take_profit_pct=0.0005,)
                        #    trading_start="00:30", trading_end="23:00")
    # 執行回測
    pf = strategy.run(df)
    
    # 輸出統計數據
    print(pf.stats())
    
    # 可視化
    pf.plot().show()