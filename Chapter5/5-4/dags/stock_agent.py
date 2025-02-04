import pandas as pd
import shioaji as sj
import datetime

class StockAPIWrapper:
    def __init__(self, api):
        self.api = api

    # 獲取持倉資料
    def get_positions(self):
        positions = self.api.list_positions(self.api.stock_account, unit=sj.constant.Unit.Share)
        now_position = pd.DataFrame(s.__dict__ for s in positions)
        return now_position

    # 獲取指定日期的行情資料 (K線)
    def get_kbars(self, stock_id, start_date, end_date):
        kbars = self.api.kbars(
            contract=self.api.Contracts.Stocks[stock_id],
            start=start_date,
            end=end_date,
        )
        price_data = pd.DataFrame({**kbars})
        price_data.ts = pd.to_datetime(price_data.ts)
        return price_data

    # 獲取指定日期的行情資料 (Ticks)
    def get_ticks(self, stock_id, date):
        ticks = self.api.ticks(
            contract=self.api.Contracts.Stocks[stock_id],
            date=date,
        )
        price_data = pd.DataFrame({**ticks})
        price_data.ts = pd.to_datetime(price_data.ts)
        return price_data

    # 下單契約
    def get_contract(self, stock_id):
        return self.api.Contracts.Stocks[stock_id]

    # 整股市場 - 市價買
    def market_buy(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Buy,
            price_type=sj.constant.StockPriceType.MKT,
            order_type=sj.constant.OrderType.IOC,
            order_lot=sj.constant.StockOrderLot.Common,
            account=self.api.stock_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    # 整股市場 - 市價賣
    def market_sell(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Sell,
            price_type=sj.constant.StockPriceType.MKT,
            order_type=sj.constant.OrderType.IOC,
            order_lot=sj.constant.StockOrderLot.Common,
            account=self.api.stock_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    # 整股市場 - 限價買
    def limit_buy(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Buy,
            price_type=sj.constant.StockPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            order_lot=sj.constant.StockOrderLot.Common,
            account=self.api.stock_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    # 整股市場 - 限價賣
    def limit_sell(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Sell,
            price_type=sj.constant.StockPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            order_lot=sj.constant.StockOrderLot.Common,
            account=self.api.stock_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    # 整股市場 - 融券放空
    def short_sell(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Sell,
            price_type=sj.constant.StockPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            order_lot=sj.constant.StockOrderLot.Common,
            order_cond='ShortSelling',
            account=self.api.stock_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    # 整股市場 - 融券回補
    def short_cover(self, contract, price, quantity):
        order = self.api.Order(
            price=price,
            quantity=quantity,
            action=sj.constant.Action.Buy,
            price_type=sj.constant.StockPriceType.LMT,
            order_type=sj.constant.OrderType.ROD,
            order_lot=sj.constant.StockOrderLot.Common,
            order_cond='ShortSelling',
            account=self.api.stock_account,
        )
        trade = self.api.place_order(contract, order)
        self.api.update_status(self.api.stock_account)
        return trade

    


class StockTradeManager(StockAPIWrapper):
    def __init__(self, api, exclude_list=None):
        super().__init__(api)
        self.exclude_list = exclude_list if exclude_list else []

    # 比對模擬倉位與真實倉位
    def sync_positions(self, simulated_position):
        start_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        if len(simulated_position) == 0:
            return
        
        simulated_position['股票'] = simulated_position['股票'].astype(str)
        # 轉換成 dictionary 方便比對
        simulated_dict = simulated_position.set_index('股票')['持倉'].to_dict()
        real_positions = self.get_positions()
        if len(real_positions) > 0:
            real_positions['code'] = real_positions['code'].astype(str)
            # 如果 direction 是 Action.Sell，將 quantity 轉為負值
            real_positions['quantity'] = real_positions.apply(
                lambda row: row['quantity'] * -1 
                if row['direction'] == sj.constant.Action.Sell else row['quantity'],
                axis=1
            )
            real_dict = real_positions.set_index('code')['quantity'].to_dict()
        else:
            real_dict = {}
        all_codes = set(simulated_dict.keys()).union(set(real_dict.keys()))

        for code in all_codes:
            code = str(code)
            if code in self.exclude_list:
                continue  # 排除清單中的股票
            simulated_size = int(simulated_dict.get(code, 0)/1000)
            real_size = int(real_dict.get(code, 0)/1000)
            contract = self.get_contract(code)
            order_price = self.get_kbars(stock_id=code, 
                                         start_date=start_date, 
                                         end_date=end_date)['Close'].tolist()[-1]
            print(f"""Processing stock {code}: 
                  Simulated size = {simulated_size}, 
                  Real size = {real_size}, 
                  Order price = {order_price}""")

            if simulated_size > 0:  # 模擬庫存 > 0
                if real_size > 0:  # 真實庫存 > 0
                    if simulated_size > real_size:  # 模擬庫存 > 真實庫存，買進補足
                        print(f"""Condition: Simulated > Real (Buy). 
                              Action: Market Buy {simulated_size - real_size} units.""")
                        self.market_buy(contract, order_price, simulated_size - real_size)

                    elif simulated_size < real_size:  # 模擬庫存 < 真實庫存，賣出補齊
                        print(f"""Condition: Simulated < Real (Sell). 
                              Action: Market Sell {real_size - simulated_size} units.""")
                        self.market_sell(contract, order_price, real_size - simulated_size)

                elif real_size < 0:  # 真實庫存 < 0
                    print(f"""Condition: Simulated > 0, Real < 0. 
                          Action: Short Cover {abs(real_size)} units, 
                          Market Buy {simulated_size} units.""")
                    self.short_cover(contract, order_price, abs(real_size))
                    self.market_buy(contract, order_price, simulated_size)


                elif real_size == 0:  # 真實庫存 = 0
                    print(f"""Condition: Simulated > 0, Real = 0. 
                          Action: Market Buy {simulated_size} units.""")
                    self.market_buy(contract, order_price, simulated_size)

            elif simulated_size < 0:  # 模擬庫存 < 0
                if real_size > 0:  # 真實庫存 > 0
                    print(f"""Condition: Simulated < 0, Real > 0. 
                          Action: Market Sell {real_size} units, 
                          Short Sell {abs(simulated_size)} units.""")
                    self.market_sell(contract, order_price, real_size)
                    self.short_sell(contract, order_price, abs(simulated_size))

                elif real_size < 0:  # 真實庫存 < 0
                    if simulated_size > real_size:  # 模擬庫存 > 真實庫存，融券回補
                        print(f"""Condition: Simulated > Real (Short Cover). 
                              Action: Short Cover {abs(real_size - simulated_size)} units.""")
                        self.short_cover(contract, order_price, abs(real_size - simulated_size))

                    elif simulated_size < real_size:  # 模擬庫存 < 真實庫存，融券放空補足
                        print(f"""Condition: Simulated < Real (Short Sell). 
                              Action: Short Sell {abs(real_size - simulated_size)} units.""")
                        self.short_sell(contract, order_price, abs(real_size - simulated_size))

                elif real_size == 0:  # 真實庫存 = 0
                    print(f"""Condition: Simulated < 0, Real = 0. 
                          Action: Short Sell {abs(simulated_size)} units.""")
                    self.short_sell(contract, order_price, abs(simulated_size))

            elif simulated_size == 0:  # 模擬庫存 = 0
                if real_size != 0:
                    print(f"""Condition: Simulated = 0, Real != 0. 
                          Action: Skipping stock {code}.""")

            print('==============================')
        print("同步完成！")



    def execute_orders(self, order_df):
        if len(order_df)==0:
            return
        real_positions = self.get_positions()

        if len(real_positions) > 0:
            real_positions['code'] = real_positions['code'].astype(str)
            real_positions['quantity'] = real_positions.apply(
                lambda row: row['quantity'] * -1 
                if row['direction'] == sj.constant.Action.Sell else row['quantity'],
                axis=1
            )
            position_dict = real_positions.set_index('code')['quantity'].to_dict()
        else:
            position_dict = {}

        for _, order in order_df.iterrows():
            stock_id = str(order['股票'])
            action = order['訂單']
            quantity = int(order['數量'] / 1000)
            contract = self.get_contract(stock_id)
            current_position = int(position_dict.get(stock_id, 0)/1000)

            start_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
            end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            latest_price = self.get_kbars(stock_id, start_date, end_date)['Close'].iloc[-1]

            if current_position == 0: 
                if action == "買進":
                    print(f"""Condition: No position, action is Buy.
                            Action: Market Buy {quantity} units at price {latest_price}.""")
                    self.market_buy(contract, latest_price, quantity)

                elif action == "賣出":
                    print(f"""Condition: No position, action is Sell.
                            Action: Short Sell {quantity} units at price {latest_price}.""")
                    self.short_sell(contract, latest_price, quantity)

            elif current_position > 0: 
                if action == "買進":
                    print(f"""Condition: Positive position, action is Buy.
                            Action: Market Buy {quantity} units at price {latest_price}.""")
                    self.market_buy(contract, latest_price, quantity)

                elif action == "賣出":
                    if quantity <= current_position:
                        print(f"""Condition: Positive position, Sell quantity <= position.
                                Action: Market Sell {quantity} units at price {latest_price}.""")
                        self.market_sell(contract, latest_price, quantity)
                        
                    else:
                        short_quantity = quantity - current_position
                        print(f"""Condition: Positive position, Sell quantity > position.
                                Action: Market Sell {current_position} units at price {latest_price}.
                                Action: Short Sell {short_quantity} units at price {latest_price}.""")
                        self.market_sell(contract, latest_price, current_position)
                        self.short_sell(contract, latest_price, short_quantity)

            elif current_position < 0: 
                if action == "買進":
                    if quantity <= abs(current_position):
                        print(f"""Condition: Negative position, Buy quantity <= position.
                                Action: Short Cover {quantity} units at price {latest_price}.""")
                        self.short_cover(contract, latest_price, quantity)
                        
                    else:
                        buy_quantity = quantity - abs(current_position)
                        print(f"""Condition: Negative position, Buy quantity > position.
                                Action: Short Cover {abs(current_position)} units at price {latest_price}.
                                Action: Market Buy {buy_quantity} units at price {latest_price}.""")
                        self.short_cover(contract, latest_price, abs(current_position))
                        self.market_buy(contract, latest_price, buy_quantity)

                elif action == "賣出":
                    print(f"""Condition: Negative position, action is Sell.
                            Action: Short Sell {quantity} units at price {latest_price}.""")
                    self.short_sell(contract, latest_price, quantity)

        print("All orders processed!")


