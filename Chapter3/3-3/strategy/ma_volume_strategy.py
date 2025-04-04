import datetime as dt
import backtrader as bt
from datetime import datetime
import calendar


class MA_Volume_Strategy(bt.Strategy):
    params = (
        ('ma_short', 3),
        ('ma_medium', 15),
        ('ma_long', 90),
        ('stddev_short', 3),
        ('stddev_long', 30),
        ('vol_ma_short', 10),
        # ('vol_ma_long', 60),
        ('vol_ma_short_threshold', 1500/60/10),
        ('stop_loss_pct',   0.00001),  
        ('take_profit_pct', 0.00005),
        ('trading_start', dt.time(9, 20)),
        ('trading_end', dt.time(10, 0)),
    )

    def log(self, txt, dt=None):
        ''' 日誌記錄函數 '''
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 收盤價
        self.dataclose = self.datas[0].close

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
        self.stddev_short = bt.indicators.StdDev(self.dataclose, period=self.params.stddev_short)
        self.stddev_long = bt.indicators.StdDev(self.dataclose, period=self.params.stddev_long)

        self.order = None

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

        status = None
        # if (
        #     self.option_expiration(self.datas[0].datetime.datetime(0)).day
        #     == self.datas[0].datetime.datetime(0).day
        # ):
        #     if self.datas[0].datetime.datetime(0).hour >= 13:
        #         status = "end"
        #         if  position_size != 0:
        #             self.close()
        #             self.log("Expired and Create Close Order")

        if status != 'end':
            if not position_size:
                # 多頭進場條件
                if (self.dataclose[0] > self.ma_short[0] and
                    self.dataclose[0] > self.ma_medium[0] and
                    self.dataclose[0] > self.ma_long[0] and
                    self.stddev_short[0] > self.stddev_long[0] and
                    self.vol_ma_short[0] > self.vol_ma_short_threshold):
                    self.order = self.buy()
                    self.log('創建買單')
                # 空頭進場條件
                elif (self.dataclose[0] < self.ma_short[0] and
                    self.dataclose[0]   < self.ma_medium[0] and
                    self.dataclose[0]   < self.ma_long[0] and
                    self.stddev_short[0] > self.stddev_long[0] and
                    self.vol_ma_short[0] > self.vol_ma_short_threshold):
                    self.order = self.sell()
                    self.log('創建賣單')
            else:
                # 已有持倉，檢查出場條件
                if position_size > 0:
                    stop_loss_price = position_price * (1 - self.params.stop_loss_pct)
                    take_profit_price = position_price * (1 + self.params.take_profit_pct)
                    # 多頭持倉
                    if self.dataclose[0] >= take_profit_price:
                        self.order = self.close()
                        self.log('平多單 - 停利')
                    elif self.dataclose[0] <= stop_loss_price:
                        self.order = self.close()
                        self.log('平多單 - 停損')

                elif position_size < 0:
                    stop_loss_price = position_price * (1 + self.params.stop_loss_pct)
                    take_profit_price = position_price * (1 - self.params.take_profit_pct)
                    # 空頭持倉
                    if self.dataclose[0] <= take_profit_price:
                        self.order = self.close()
                        self.log('平空單 - 停利')
                    elif self.dataclose[0] >= stop_loss_price:
                        self.order = self.close()
                        self.log('平空單 - 停損')