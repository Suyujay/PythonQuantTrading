import pandas as pd
import shioaji as sj
import datetime

class FuturesAPIWrapper:
    def __init__(self, api):
        self.api = api

    # 獲取持倉資料
    def get_positions(self):
        positions = self.api.list_positions(self.api.futopt_account)
        now_position = pd.DataFrame(s.__dict__ for s in positions)
        return now_position

    # 獲取指定日期的行情資料 (K線)
    def get_kbars(self, contract, start_date, end_date):
        kbars = self.api.kbars(
            contract=contract,
            start=start_date,
            end=end_date,
        )
        price_data = pd.DataFrame({**kbars})
        price_data.ts = pd.to_datetime(price_data.ts)
        return price_data

    # 整股市場 - 市價買
    def market_buy(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Buy,
            price_type=sj.constant.FuturesPriceType.MKT,
            order_type=sj.constant.OrderType.IOC,
            octype=sj.constant.FuturesOCType.Auto,
            account=self.api.futopt_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.futopt_account)
        return trade

    # 整股市場 - 市價賣
    def market_sell(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Sell,
            price_type=sj.constant.FuturesPriceType.MKT,
            order_type=sj.constant.OrderType.IOC,
            octype=sj.constant.FuturesOCType.Auto,
            account=self.api.futopt_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.futopt_account)
        return trade

    # 整股市場 - 限價買
    def limit_buy(self, contract, price, quantity):
        order = self.api.Order(
            action=sj.constant.Action.Buy,
            price=price,
            quantity=quantity,
            price_type=sj.constant.FuturesPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            octype=sj.constant.FuturesOCType.Auto,
            account=self.api.futopt_account
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    # 整股市場 - 限價賣
    def limit_sell(self, contract, price, quantity):
        order = self.api.Order(
            action=sj.constant.Action.Sell,
            price=price,
            quantity=quantity,
            price_type=sj.constant.FuturesPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            octype=sj.constant.FuturesOCType.Auto,
            account=self.api.futopt_account
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade


class FuturesTradeManager(FuturesAPIWrapper):
    def __init__(self, api, contract):
        super().__init__(api)
        self.contract = contract
        self.target_code = contract.target_code

    def sync_positions(self, simulated_position):
        start_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        if len(simulated_position) == 0:
            simulated_position=0
        
        simulated_position = simulated_position['持倉數量'].tolist()[-1]
        real_positions = self.get_positions()
        if len(real_positions) > 0:
            real_positions = real_positions[real_positions['code']==self.target_code]
            if len(real_positions) >0:
                real_positions['quantity'] = real_positions.apply(
                    lambda row: row['quantity'] * -1 
                    if row['direction'] == sj.constant.Action.Sell else row['quantity'],
                    axis=1
                )
                real_positions = real_positions['quantity'].tolist()[-1]
            else:
                real_positions = 0
        else:
            real_positions = 0

        process_order = simulated_position-real_positions
        order_price = self.get_kbars(contract=self.contract, 
                                        start_date=start_date, 
                                        end_date=end_date)['Close'].tolist()[-1]
        print(f"""Processing contract {self.target_code}: 
                Simulated size = {simulated_position}, 
                Real size = {real_positions}, 
                Order size = {process_order}""")
        
        if process_order > 0:
            print(f"""Action: Market Buy {process_order}.""")
            self.market_buy(self.contract, order_price, abs(process_order))
        elif process_order < 0:
            print(f"""Action: Market Sell {process_order}.""")
            self.market_sell(self.contract, order_price, abs(process_order))
        print("同步完成！")

    def execute_orders(self, order_df):
        if len(order_df)==0:
            return
        action = order_df['訂單'].tolist()[0]
        quantity = order_df['數量'].tolist()[0]
        start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        order_price = self.get_kbars(self.contract, start_date, end_date)['Close'].iloc[-1]

        if action =="買進":
            self.market_buy(self.contract, order_price, abs(quantity))
        elif action == "賣出":
            self.market_sell(self.contract, order_price, abs(quantity))
        print("All orders  processed!")


