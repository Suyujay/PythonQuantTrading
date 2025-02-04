
# 1.code 用函數包裝起來
# 2.將 line 通知加入 order callback
def execute_stock_trade():
    from stock_agent import StockAPIWrapper
    import pandas as pd
    import shioaji as sj
    import os
    from tool import send_line_message
    import time
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pfx_path = os.path.join(current_dir, "Sinopac.pfx")
    api = sj.Shioaji(simulation=True) 

    api.login(
        api_key="",
        secret_key="",
    )

    api.activate_ca(
        ca_path=pfx_path,
        ca_passwd="",
        person_id="",
    )


    def order_cb(stat, msg):
        response_code = send_line_message('交易回報：'+str(msg))
        print(stat, msg)
        
    api.set_order_callback(order_cb)
    #%%
    api_wrapper = StockAPIWrapper(api)

    positions = api_wrapper.get_positions()
    print(positions)

    #%%
    from stock_agent import StockAPIWrapper,StockTradeManager
    simulated_position = pd.read_excel('position.xlsx')
    stock_manager = StockTradeManager(api)
    stock_manager.sync_positions(simulated_position=simulated_position)


    #%%
    order_df = pd.read_excel('order.xlsx')
    stock_manager.execute_orders(order_df=order_df)
    time.sleep(3)
