from tool import send_line_message
import shioaji as sj
import os
# def order_cb(stat, msg):
#     action = msg['order']['action']
#     price = msg['order']['price']
#     code = msg['contract']['code']
#     # 組成字串
#     result = f"{action} at {price} for {code}"
#     send_line_message(str(result))
#     print(stat, msg)

def order_cb(stat, msg):
    send_line_message(str(msg))
    print(stat, msg)


api = sj.Shioaji(simulation=True) 


api.login(
    api_key="api_key",
    secret_key="api_key",
)

current_dir = os.path.dirname(os.path.abspath(__file__))
pfx_path = os.path.join(current_dir, "Sinopac.pfx")
api.activate_ca(
    ca_path=pfx_path,
    ca_passwd="PERSON_ID",
    person_id="PERSON_ID",
)


api.set_order_callback(order_cb)

#下單契約
contract = api.Contracts.Stocks[str('1102')]
# #整股市場 - 市價買
order = api.Order(
    price=31.75,
    quantity=int(1),
    action=sj.constant.Action.Buy,
    price_type=sj.constant.StockPriceType.MKT,
    order_type=sj.constant.OrderType.IOC,
    order_lot=sj.constant.StockOrderLot.Common,
    account=api.stock_account,
)
trade = api.place_order(contract, order)
api.update_status(api.stock_account)

import time
time.sleep(3)
api.logout()

