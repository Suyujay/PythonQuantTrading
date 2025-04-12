import datetime as dt
import backtrader as bt
from datetime import datetime
import calendar


class MA_Volume_Strategy(bt.Strategy):
    params = (
        ('ma_short', 3),
        ('ma_medium', 15),
        ('ma_long', 50),
        ('stddev_short', 3),
        ('stddev_long', 30),
        ('vol_ma_short', 10),
        # ('vol_ma_long', 60),
        ('vol_ma_short_threshold', 1500),
        ('prev_high_period', 20),  # 新增：前高週期
        ('prev_low_period', 20),   # 新增：前低週期
        ('atr_short_period', 20),        # ATR 週期
        ('atr_long_period', 1000),        # ATR 週期
        ('atr_threshold_high', 0.05), # ATR 高閾值 (用於判斷大振幅)
        ('atr_threshold_low', 3),  # ATR 低閾值 (用於判斷小振幅)
        ('vol_threshold_low', 500), # 成交量低閾值 (用於判斷小量)
        ('stop_loss_pct',   0.00001),  
        ('take_profit_pct', 0.00005),
        ('trading_start', dt.time(0, 00)),
        ('trading_end', dt.time(23, 59)),
    )

    def log(self, txt, dt=None):
        ''' 日誌記錄函數 '''
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 收盤價
        self.dataclose = self.datas[0].close
        # 最高價
        self.datahigh = self.datas[0].high
        # 最低價
        self.datalow = self.datas[0].low

        # 成交量
        self.datavolume = self.datas[0].volume

        # 移動平均線
        self.ma_short = bt.indicators.SMA(self.dataclose, period=self.params.ma_short)
        self.ma_medium = bt.indicators.SMA(self.dataclose, period=self.params.ma_medium)
        self.ma_long = bt.indicators.SMA(self.dataclose, period=self.params.ma_long)

        # 成交量移動平均線
        self.vol_ma_short = bt.indicators.SMA(self.datavolume, period=self.params.vol_ma_short)
        # self.vol_ma_long = bt.indicators.SMA(self.datavolume, period=self.params.vol_ma_long)
        self.vol_ma_short_threshold = self.params.vol_ma_short_threshold

        # 標準差
        # self.stddev_short = bt.indicators.StdDev(self.dataclose, period=self.params.stddev_short)
        # self.stddev_long = bt.indicators.StdDev(self.dataclose, period=self.params.stddev_long)

        # 新增：前高前低指標
        # self.prev_high = bt.indicators.Highest(self.datahigh, period=self.params.prev_high_period)
        # self.prev_low = bt.indicators.Lowest(self.datalow, period=self.params.prev_low_period)

        # 
        # self.mom = bt.indicators.Momentum(self.dataclose, period=self.params.ma_short)
        self.mosc_short = bt.indicators.MomentumOscillator(self.dataclose, period=self.params.ma_medium)
        # self.rmi_long = bt.indicators.RelativeMomentumIndex(self.dataclose, period=self.params.ma_medium)

        # 新增：ATR 指標
        self.atr = bt.indicators.ATR(self.datas[0], period=self.params.atr_short_period)
        self.atr_ratio = self.atr / self.dataclose * 100
        # self.atr_long = bt.indicators.ATR(self.datas[0], period=self.params.atr_long_period)

        self.order = None

    def is_uptrend(self):
        """檢查是否滿足多頭順勢條件"""
        return (self.dataclose[0] > self.ma_short[0] and
                self.ma_short[0]  > self.ma_medium[0] and
                self.ma_medium[0] > self.ma_long[0] and
                # self.stddev_short[0] > self.stddev_long[0] and
                self.atr_ratio[0] > self.params.atr_threshold_high and
                self.mosc_short[0] > 100 and
                self.vol_ma_short[0] > self.vol_ma_short_threshold)
    
    def is_downtrend(self):
        """檢查是否滿足空頭順勢條件"""
        return (self.dataclose[0] < self.ma_short[0] and
                self.ma_short[0]  < self.ma_medium[0] and
                self.ma_medium[0] < self.ma_long[0] and
                # self.stddev_short[0] > self.stddev_long[0] and
                self.atr_ratio[0] > self.params.atr_threshold_high and
                self.mosc_short[0] < 100 and
                self.vol_ma_short[0] > self.vol_ma_short_threshold)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'''BUY EXECUTED, Price: {order.executed.price:.2f}, 
                         Cost: {order.executed.value:.2f}, 
                         Comm {order.executed.comm:.2f}''')
                self.buycomm = order.executed.comm
            else:
                self.sellprice = order.executed.price
                self.log(f'''SELL EXECUTED, Price: {order.executed.price:.2f},
                          Cost: {order.executed.value:.2f}, 
                          Comm {order.executed.comm:.2f}''')
            self.bar_executed = len(self)
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    @staticmethod
    def option_expiration(date): 
        # print(f"Option expiration date: {date}")
        day = 21 - (calendar.weekday(date.year, date.month, 1) + 4) % 7 
        return datetime(date.year, date.month, day)

    def check_trading_time(self):
        """檢查當前是否在交易時段內，並在交易時段結束時平倉"""
        current_time = self.datas[0].datetime.datetime(0).time()
        position_size = self.getposition().size
            
        # 檢查是否在交易時段內
        is_in_session = (
            (current_time.hour > self.params.trading_start.hour or 
             (current_time.hour == self.params.trading_start.hour and 
              current_time.minute >= self.params.trading_start.minute)) and
            (current_time.hour < self.params.trading_end.hour or 
             (current_time.hour == self.params.trading_end.hour and 
              current_time.minute < self.params.trading_end.minute))
        )

        # 如果不是交易時段且有持倉，則平倉
        if not is_in_session and position_size != 0:
            self.log(f'平倉時間: {current_time}, 當前持倉: {position_size}')
            self.close()
            self.log('交易時段結束平倉')
            return False
        
        return is_in_session

    def next(self):
        if self.order:
            return

        position_size = self.getposition().size
        position_price = self.getposition().price

        # 首先檢查交易時段
        if not self.check_trading_time():
            return

        # status = None
        # if (
        #     self.option_expiration(self.datas[0].datetime.datetime(0)).day
        #     == self.datas[0].datetime.datetime(0).day
        # ):
        #     if self.datas[0].datetime.datetime(0).hour >= 13:
        #         status = "end"
        #         if  position_size != 0:
        #             self.close()
        #             self.log("Expired and Create Close Order")

        # if status != 'end':
        # --- 判斷市場狀態 ---
        is_high_volume = self.vol_ma_short[0] > self.vol_ma_short_threshold
        is_low_volume = self.vol_ma_short[0] < self.params.vol_threshold_low

        # is_high_volatility = self.stddev_short[0] > self.stddev_long[0]
        # 假設低波動率是短標準差不大於長標準差
        # is_low_volatility = self.stddev_short[0] <= self.stddev_long[0]

        # is_large_amplitude = self.atr[0] > self.params.atr_threshold_high
        # is_small_amplitude = self.atr[0] < self.params.atr_threshold_low

        # 判斷交易模式
        # trend_following_mode = is_high_volume and is_high_volatility and is_large_amplitude
        trend_following_mode = True
        # counter_trend_mode = is_low_volume and is_low_volatility and is_small_amplitude
        # --- 狀態判斷結束 ---

        if not position_size:
            # --- 進場邏輯 ---
            # 方法 2: 檢查 datas[1] 的長度是否增加 (更常用)
            if trend_following_mode:
                # 順勢交易模式
                if self.is_uptrend(): # 突破昨日高點
                    self.order = self.buy()
                    self.log('創建買單 (順勢)')
                elif self.is_downtrend(): # 跌破昨日低點
                    self.order = self.sell()
                    self.log('創建賣單 (順勢)')

            # elif counter_trend_mode:
            #     # 逆勢交易模式 (範例：觸及前低買入，觸及前高賣出)
            #     # 注意：這裡的逆勢邏輯非常簡化，實際應用需要更精確的反轉信號
            #     if self.datalow[0] <= self.prev_low[-1]: # 觸及或跌破前低
            #         # 可以加入反轉確認，例如收盤價高於最低價
            #         if self.dataclose[0] > self.datalow[0]:
            #             self.order = self.buy()
            #             self.log('創建買單 (逆勢 - 觸及前低)')
            #     elif self.datahigh[0] >= self.prev_high[-1]: # 觸及或突破前高
            #         # 可以加入反轉確認，例如收盤價低於最高價
            #         if self.dataclose[0] < self.datahigh[0]:
            #             self.order = self.sell()
            #             self.log('創建賣單 (逆勢 - 觸及前高)')

        else:
            # 已有持倉，檢查出場條件
            if position_size > 0:
                stop_loss_price = position_price * (1 - self.params.stop_loss_pct)
                take_profit_price = position_price * (1 + self.params.take_profit_pct)
                # 多頭持倉
                if self.dataclose >= take_profit_price:
                    self.order = self.close()
                    self.log('平多單 - 停利')
                elif self.dataclose <= stop_loss_price:
                    self.order = self.close()
                    self.log('平多單 - 停損')
            elif position_size < 0:
                stop_loss_price = position_price * (1 + self.params.stop_loss_pct)
                take_profit_price = position_price * (1 - self.params.take_profit_pct)
                # 空頭持倉
                if self.dataclose <= take_profit_price:
                    self.order = self.close()
                    self.log('平空單 - 停利')
                elif self.dataclose >= stop_loss_price:
                    self.order = self.close()
                    self.log('平空單 - 停損')