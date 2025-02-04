#%%
import shioaji as sj
import pandas as pd

api = sj.Shioaji(simulation=True) 

api.login(
    api_key="",
    secret_key="",
)

import os
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir)
pfx_path = os.path.join(current_dir, "Sinopac.pfx")
print(pfx_path)

api.activate_ca(
    ca_path=pfx_path,
    ca_passwd="",
    person_id="",
)
#%%
#獲取持倉
positions = api.list_positions(api.stock_account, unit=sj.constant.Unit.Share)
now_position = pd.DataFrame(s.__dict__ for s in positions)
print(now_position)

#%%
#獲取行情資料
ticks = api.ticks(
    contract=api.Contracts.Stocks["2330"], 
    date='2024-11-08'
    )
price_data = pd.DataFrame({**ticks})
price_data.ts = pd.to_datetime(price_data.ts)
print(price_data)

#%%
#獲取行情資料
kbars = api.kbars(
    contract=api.Contracts.Stocks["2330"], 
    start="2024-11-24", 
    end="2024-11-28", 
)
price_data = pd.DataFrame({**kbars})
price_data.ts = pd.to_datetime(price_data.ts)
print(price_data)


#%%
#下單契約
contract = api.Contracts.Stocks[str('2330')]
print(contract)

#%%
# #整股市場 - 市價買
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(1),
    action=sj.constant.Action.Buy,
    price_type=sj.constant.StockPriceType.MKT,
    order_type=sj.constant.OrderType.IOC,
    order_lot=sj.constant.StockOrderLot.Common,
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)
#%%
# #整股市場 - 市價賣
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(1),
    action=sj.constant.Action.Sell,
    price_type=sj.constant.StockPriceType.MKT,
    order_type=sj.constant.OrderType.IOC,
    order_lot=sj.constant.StockOrderLot.Common,
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)

#%%
#整股市場 - Limit 單買
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(1),
    action=sj.constant.Action.Buy,
    price_type=sj.constant.StockPriceType.LMT,
    order_type=sj.constant.OrderType.ROD,
    order_lot=sj.constant.StockOrderLot.Common,
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)
print(api.list_trades())
#%%
# #整股市場 - Limit 單賣
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(1),
    action=sj.constant.Action.Sell,
    price_type=sj.constant.StockPriceType.LMT,
    order_type=sj.constant.OrderType.ROD,
    order_lot=sj.constant.StockOrderLot.Common,
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)

#%%
# #整股市場 - 融券放空
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(1),
    action=sj.constant.Action.Sell,
    price_type=sj.constant.StockPriceType.LMT,
    order_type=sj.constant.OrderType.ROD,
    order_lot=sj.constant.StockOrderLot.Common,
    order_cond='ShortSelling',
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)

#%%
# #整股市場 - 融券回補
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(2),
    action=sj.constant.Action.Buy,
    price_type=sj.constant.StockPriceType.LMT,
    order_type=sj.constant.OrderType.ROD,
    order_lot=sj.constant.StockOrderLot.Common,
    order_cond='ShortSelling',
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)


#%%
#零股市場 - Limit 單買
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(10),
    action=sj.constant.Action.Buy,
    price_type=sj.constant.StockPriceType.LMT,
    order_type=sj.constant.OrderType.ROD,
    order_lot=sj.constant.StockOrderLot.IntradayOdd, 
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)

#%%

#零股市場 - Limit 單賣
order = api.Order(
    price=price_data['Close'].tolist()[-1],
    quantity=int(10),
    action=sj.constant.Action.Sell,
    price_type=sj.constant.StockPriceType.LMT,
    order_type=sj.constant.OrderType.ROD,
    order_lot=sj.constant.StockOrderLot.IntradayOdd, 
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)
print(trade)
# %%
