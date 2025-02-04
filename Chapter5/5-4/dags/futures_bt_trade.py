# 1.將整個 code 用函數包起來
# 2.移除 pyfolio 相關的東西
# 3. import 我們的 sned_line_message 進來
# 4. 確認交易日期以及交易相關設定
# 5. 在 stop 中增加 line messaging

def get_futures_trade_list():
    import datetime  
    import backtrader as bt
    import pandas as pd
    import calendar
    import warnings
    # 5-2 import 需要的套件
    from futures_agent import FuturesAPIWrapper
    from datetime import datetime ,timedelta
    warnings.filterwarnings('ignore')
    # 5-2 調整，登入 shioaji
    import shioaji as sj
    import os 
    from tool import send_line_message
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pfx_path = os.path.join(current_dir, "Sinopac.pfx")
    api = sj.Shioaji(simulation=True) 
    api.login(
        api_key="",
        secret_key="",
    )
    print('登入成功')
    api.activate_ca(
        ca_path=pfx_path,
        ca_passwd="",
        person_id="",
    )
    print('ca 啟動成功')

    # 5-2 定義自己喜歡的策略開始日
    LIVE_TRADE_START = '2025-01-20'


    def option_expiration(date): 
        day = 21 - (calendar.weekday(date.year, date.month, 1) + 4) % 7 
        return datetime(date.year, date.month, day) 

    class MA_Volume_Strategy(bt.Strategy):
        params = (
            ('ma_short', 3),
            ('ma_medium', 20),
            ('ma_long', 60),
            ('stop_loss_pct', 0.02),  
            ('take_profit_pct', 0.02), 
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
            self.vol_ma_short = bt.indicators.SMA(self.datavolume, period=self.params.ma_short)
            self.vol_ma_long = bt.indicators.SMA(self.datavolume, period=self.params.ma_long)
            # 5-2 調整，新增 order_trace
            self.order_list = []

        # 5-2 調整，新增 custom_notify_order
        def custom_notify_order(self, order):
            if order:
                if order.status in [order.Submitted, order.Accepted]:
                    self.order_list.append(order)
                elif order.status == order.Completed:
                    if order.isbuy():
                        self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                                f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                    else:
                        self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                                f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                    self.order = None


        def notify_trade(self, trade):
            if not trade.isclosed:
                return
            self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

        def next(self):
            self.order_list=[]
            # 5-2 調整
            if self.datas[0].datetime.datetime(0) >=datetime.strptime(LIVE_TRADE_START, '%Y-%m-%d'):
                position_size = self.getposition().size
                position_price = self.getposition().price

                # 不更動策略核心邏輯
                if (
                    option_expiration(self.datas[0].datetime.datetime(0)).day
                    == self.datas[0].datetime.datetime(0).day
                ):
                    if self.datas[0].datetime.datetime(0).hour >= 13:
                        if position_size != 0:
                            order = self.close()
                            self.log("Expired and Create Close Order")
                            self.custom_notify_order(order)
                        return

                # 無持倉情況
                if position_size == 0:
                    # 多頭進場條件
                    if (self.dataclose[0] > self.ma_short[0] and
                        self.dataclose[0] > self.ma_medium[0] and
                        self.dataclose[0] > self.ma_long[0] and
                        self.vol_ma_short[0] > self.vol_ma_long[0]):
                        order = self.buy()
                        self.log('創建買單')
                        self.custom_notify_order(order)

                    # 空頭進場條件
                    elif (self.dataclose[0] < self.ma_short[0] and
                        self.dataclose[0] < self.ma_medium[0] and
                        self.dataclose[0] < self.ma_long[0] and
                        self.vol_ma_short[0] < self.vol_ma_long[0]):
                        order = self.sell()
                        self.log('創建賣單')
                        self.custom_notify_order(order)

                # 已有持倉情況
                else:
                    if position_size > 0:
                        # 多頭
                        stop_loss_price = position_price * (1 - self.params.stop_loss_pct)
                        take_profit_price = position_price * (1 + self.params.take_profit_pct)
                        if self.dataclose[0] >= take_profit_price:
                            order = self.close()
                            self.log('平多單 - 停利')
                            self.custom_notify_order(order)
                        elif self.dataclose[0] <= stop_loss_price:
                            order = self.close()
                            self.log('平多單 - 停損')
                            self.custom_notify_order(order)

                    elif position_size < 0:
                        # 空頭
                        stop_loss_price = position_price * (1 + self.params.stop_loss_pct)
                        take_profit_price = position_price * (1 - self.params.take_profit_pct)
                        if self.dataclose[0] <= take_profit_price:
                            order = self.close()
                            self.log('平空單 - 停利')
                            self.custom_notify_order(order)
                        elif self.dataclose[0] >= stop_loss_price:
                            order = self.close()
                            self.log('平空單 - 停損')
                            self.custom_notify_order(order)

        # 5-2 調整，stop 函數
        def stop(self):
            # 回測結束時輸出最終持倉與最後一筆訂單動作
            print("當前持倉:")
            positions_data = []
            position = self.getposition()
            if position.size != 0:
                print(f"合約持倉: {position.size} 口, 成本: {position.price}")
                send_line_message(f'期貨持倉:合約持倉: {position.size} 口, 成本: {position.price}')
                positions_data.append({
                    "合約": self.datas[0]._name,
                    "持倉數量": position.size,
                    "持倉成本": position.price
                })
            else:
                print("無持倉")

            print('=============最後一筆訂單動作=============')
            orders_data = []
            for order in self.order_list:
                action = '買進' if order.isbuy() else '賣出'
                print(f"合約: Futures, 訂單: {action} {abs(order.size)} 口")
                send_line_message(f'期貨order:"合約: Futures, 訂單: {action} {abs(order.size)} 口')
                orders_data.append({
                    "合約": order.data._name,
                    "訂單": action,
                    "數量": abs(order.size),
                })

            positions_df = pd.DataFrame(positions_data)
            positions_df.to_excel("futures_position.xlsx", index=False)

            orders_df = pd.DataFrame(orders_data)
            orders_df.to_excel("futures_order.xlsx", index=False)

    # 初始化 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 5-2 調整，獲取起訖日
    today = datetime.today()
    start_date = today - timedelta(days=30)
    today = today.strftime('%Y-%m-%d')
    start_date = start_date.strftime('%Y-%m-%d')

    # 5-2 調整， 獲取數據
    FuturesWrapper = FuturesAPIWrapper(api=api)
    data = FuturesWrapper.get_kbars(contract=api.Contracts.Futures.MXF.MXFR1,
                                start_date=start_date,
                                end_date=today)
    data = data.rename(columns={'ts':'Date'})

    # 5-2 調整，只保留日盤並且做成 30 分 K
    data.index = pd.to_datetime(data['Date'])
    data = data.between_time('08:45', '13:45')
    data = data.resample('30min', closed='right', label='right', offset='15min').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    data = data.reset_index()
    data = data.dropna()

    # 5-2 調整，取得最新的資料長度
    data = data.iloc[:-1]


    data_feed = bt.feeds.PandasData(
        dataname=data,
        name='MXF',
        datetime=0,
        high=2,
        low=3,
        open=1,
        close=4,
        volume=5,
        plot=False,
    )
    cerebro.adddata(data_feed, name='MXF')

    # 添加策略
    cerebro.addstrategy(MA_Volume_Strategy)

    # 設定初始資金和交易成本
    cerebro.broker.setcash(250000.0)
    cerebro.broker.setcommission(commission=70, margin=62000, mult=50)
    print('初始資產價值: %.2f' % cerebro.broker.getvalue())
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    # 執行回測
    results = cerebro.run()
    print('最終資產價值: %.2f' % cerebro.broker.getvalue())

