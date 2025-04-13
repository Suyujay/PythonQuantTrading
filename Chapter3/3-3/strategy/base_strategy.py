# filepath: d:\Quant\PythonQuantTrading\Chapter3\3-3\strategy\base_strategy.py
import datetime as dt
import backtrader as bt
from datetime import datetime, timedelta
import calendar

class BaseStrategy(bt.Strategy):
    """
    基礎策略類別，包含共享的參數、指標和通用方法。
    """
    params = (
        # --- 共享參數 ---
        ('ma_short', 3),
        ('ma_medium', 15),
        ('ma_long', 50),
        ('stddev_period', 20),
        ('stddev_mosc_threshold', 2.0),
        ('vol_ma_short', 10),
        ('vol_ma_short_threshold', 1500),
        ('atr_short_period', 20),
        ('atr_long_period', 1000), # 根據需要調整或移除
        ('atr_threshold_high', 0.05), # 順勢用
        ('atr_threshold_low', 0.02),  # 逆勢用 (假設)
        ('mosc_period', 15), # 動量震盪週期
        ('stop_loss_pct',   0.00001),
        ('take_profit_pct', 0.00005),
        ('trading_start', dt.time(0, 00)),
        ('trading_end', dt.time(23, 59)),
        # --- 可能特定策略需要的參數 (也可以放在子類別) ---
        ('rsi_period', 14),
        ('bbands_period', 20),
        ('bbands_devfactor', 2.0),
        ('prev_high_short', 5),
        ('prev_high_long', 20),
        ('prev_low_short', 5),
        ('prev_low_long', 20),
        # --- 連續虧損暫停相關參數 ---
        ('consecutive_loss_threshold', 2), # 連續虧損次數閾值
        ('pause_duration_minutes', 30),   # 暫停交易分鐘數
    )

    def log(self, txt, dt=None):
        ''' 日誌記錄函數 '''
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} [{self.__class__.__name__}], {txt}') # 加入類別名稱

    def __init__(self):
        # --- 獲取數據線 ---
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        # --- 計算共享指標 ---
        self.ma_short = bt.indicators.SMA(self.dataclose, period=self.params.ma_short)
        self.ma_medium = bt.indicators.SMA(self.dataclose, period=self.params.ma_medium)
        self.ma_long = bt.indicators.SMA(self.dataclose, period=self.params.ma_long)
        self.vol_ma_short = bt.indicators.SMA(self.datavolume, period=self.params.vol_ma_short)
        self.stddev = bt.indicators.StandardDeviation(self.dataclose, period=self.params.stddev_period)
        self.stddev_mosc = bt.indicators.MomentumOscillator(self.stddev, period=self.params.stddev_period)
        self.mosc = bt.indicators.MomentumOscillator(self.dataclose, period=self.params.mosc_period)
        self.atr = bt.indicators.ATR(self.datas[0], period=self.params.atr_short_period)
        self.atr_ratio = self.atr / self.dataclose * 100

        # --- 可能特定策略需要的指標 (也可以放在子類別的 __init__) ---
        self.rsi = bt.indicators.RSI(self.dataclose, period=self.params.rsi_period)
        self.bbands = bt.indicators.BollingerBands(self.dataclose,
                                                   period=self.params.bbands_period,
                                                   devfactor=self.params.bbands_devfactor)
        self.prev_high_short = bt.indicators.Highest(self.datahigh, period=self.params.prev_high_short)
        self.prev_high_long = bt.indicators.Highest(self.datahigh, period=self.params.prev_high_long)
        self.prev_low_short = bt.indicators.Lowest(self.datalow, period=self.params.prev_low_short)
        self.prev_low_long = bt.indicators.Lowest(self.datalow, period=self.params.prev_low_long)

        # --- 訂單和交易狀態 ---
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sellprice = None # 用於記錄空單價格

        # --- 連續虧損和暫停狀態 ---
        self.consecutive_losses = 0
        self.pause_until = None # 記錄暫停結束的時間

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'''BUY EXECUTED, Price: {order.executed.price:.2f}, 
                         Cost: {order.executed.value:.2f}, 
                         Comm: {order.executed.comm:.2f}''')
                self.buyprice = order.executed.price # 記錄買入價
                self.buycomm = order.executed.comm
            elif order.issell(): # 檢查是否為賣單
                self.log(f'''SELL EXECUTED, Price: {order.executed.price:.2f}, 
                         Cost: {order.executed.value:.2f}, 
                         Comm: {order.executed.comm:.2f}''')
                self.sellprice = order.executed.price # 記錄賣出價
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: {order.getstatusname()}')
        self.order = None # 重置訂單狀態

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        
        # 更新連續虧損狀態
        self._update_consecutive_losses(trade)

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def _update_consecutive_losses(self, trade):
        """根據交易結果更新連續虧損計數和觀察期狀態。"""
        current_dt = self.datas[0].datetime.datetime(0) # 獲取當前時間

        if trade.pnlcomm < 0: # 交易虧損
            self.consecutive_losses += 1
            self.log(f'交易虧損, 連續虧損次數: {self.consecutive_losses}')
            if self.consecutive_losses >= self.params.consecutive_loss_threshold:
                self.pause_until = current_dt + timedelta(minutes=self.params.pause_duration_minutes)
                self.log(f'連續虧損達到 {self.params.consecutive_loss_threshold} 次，進入觀察期直到 {self.pause_until.isoformat()}')
        else: # 交易盈利或持平
            if self.consecutive_losses > 0:
                self.log(f'交易盈利或持平，重置連續虧損計數 (之前為 {self.consecutive_losses})')
                self.consecutive_losses = 0 # 重置連續虧損計數

    def observe_pause(self):
        """檢查是否處於連續虧損後的觀察期(暫停交易)。"""
        if self.pause_until is None:
            return False # 沒有在觀察期

        current_dt = self.datas[0].datetime.datetime(0)
        if current_dt < self.pause_until:
            # self.log(f'觀察期內，暫停交易直到 {self.pause_until.isoformat()}') # 可選日誌
            return True # 仍在觀察期內
        else:
            self.log(f'觀察期結束 ({self.pause_until.isoformat()})，恢復交易')
            self.pause_until = None
            self.consecutive_losses = 0 # 觀察期結束後重置計數器
            return False # 觀察期剛結束

    @staticmethod
    def option_expiration(date): 
        # print(f"Option expiration date: {date}")
        day = 21 - (calendar.weekday(date.year, date.month, 1) + 4) % 7 
        return datetime(date.year, date.month, day)

    def check_trading_time(self):
        """檢查當前是否在交易時段內，並在交易時段結束時平倉"""
        current_time = self.datas[0].datetime.datetime(0).time()
        position_size = self.getposition().size

        is_in_session = (
            (current_time >= self.params.trading_start) and
            (current_time < self.params.trading_end)
        )

        if not is_in_session and position_size != 0:
            self.log(f'交易時段結束 ({current_time})，平倉')
            self.close() # 觸發平倉
            return False # 不在交易時段

        return is_in_session # 在交易時段

    # --- 可以在這裡定義通用的出場邏輯，或在子類別中覆寫 ---
    def manage_position(self):
        """通用倉位管理邏輯 (停損/停利)"""
        position_size = self.getposition().size
        if position_size == 0:
            return False # 沒有倉位需要管理

        entry_price = self.buyprice if position_size > 0 else self.sellprice
        if entry_price is None: # 確保有入場價格
             return False

        current_price = self.dataclose[0]
        pnl_pct = (current_price - entry_price) / entry_price if position_size > 0 else (entry_price - current_price) / entry_price

        if position_size > 0: # 多頭
            stop_loss_price = entry_price * (1 - self.params.stop_loss_pct)
            take_profit_price = entry_price * (1 + self.params.take_profit_pct)
            if current_price <= stop_loss_price:
                self.log(f'多單停損觸發 @ {current_price:.2f}')
                self.close()
                return True
            if current_price >= take_profit_price:
                self.log(f'多單停利觸發 @ {current_price:.2f}')
                self.close()
                return True
        elif position_size < 0: # 空頭
            stop_loss_price = entry_price * (1 + self.params.stop_loss_pct)
            take_profit_price = entry_price * (1 - self.params.take_profit_pct)
            if current_price >= stop_loss_price:
                self.log(f'空單停損觸發 @ {current_price:.2f}')
                self.close()
                return True
            if current_price <= take_profit_price:
                self.log(f'空單停利觸發 @ {current_price:.2f}')
                self.close()
                return True
        return False # 未觸發停損停利
