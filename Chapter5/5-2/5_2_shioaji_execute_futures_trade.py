#%%
from futures_agent import FuturesAPIWrapper,FuturesTradeManager
import pandas as pd
import shioaji as sj
import os

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

#%%
api_wrapper = FuturesAPIWrapper(api)

positions = api_wrapper.get_positions()
print(positions)
#%%
# 獲取行情資料
price_data = api_wrapper.get_kbars(contract=api.Contracts.Futures.MXF.MXFR1,
                                    start_date="2024-12-26", 
                                    end_date="2024-12-27")
print(price_data)

#%%
simulated_position = pd.read_excel('futures_position.xlsx')
print(simulated_position)
futures_manager = FuturesTradeManager(api=api, 
                                      contract=api.Contracts.Futures.MXF.MXFR1)
futures_manager.sync_positions(simulated_position=simulated_position)


#%%
order_df = pd.read_excel('futures_order.xlsx')
futures_manager.execute_orders(order_df=order_df)

# %%
