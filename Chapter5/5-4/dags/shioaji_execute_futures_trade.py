# 1.code 用函數包裝起來
# 2.將 line 通知加入 order callback

def execute_futures_trade():
    from futures_agent import FuturesAPIWrapper,FuturesTradeManager
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
    print('登入成功')
    api.activate_ca(
        ca_path=pfx_path,
        ca_passwd="",
        person_id="",
    )
    print('ca 啟動成功')

    def place_cb(stat, msg):
        send_line_message(messages=str(msg))
        print(stat, msg)

    api.set_order_callback(place_cb) 

    #%%
    api_wrapper = FuturesAPIWrapper(api)

    positions = api_wrapper.get_positions()
    print(positions)

    #%%
    simulated_position = pd.read_excel('futures_position.xlsx')
    print(simulated_position)
    futures_manager = FuturesTradeManager(api=api, 
                                        contract=api.Contracts.Futures.TMF.TMFR1)
    futures_manager.sync_positions(simulated_position=simulated_position)


    #%%
    order_df = pd.read_excel('futures_order.xlsx')
    futures_manager.execute_orders(order_df=order_df)
    print('輸出完成')
    time.sleep(3)
    # %%
