#%%
from stock_agent import StockAPIWrapper
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
api_wrapper = StockAPIWrapper(api)

positions = api_wrapper.get_positions()
print(positions)

#%%
# 獲取行情資料
price_data = api_wrapper.get_kbars("2330", "2024-11-08", "2024-11-08")
print(price_data)

#%%
from stock_agent import StockAPIWrapper,StockTradeManager
simulated_position = pd.read_excel('position.xlsx')
stock_manager = StockTradeManager(api)
stock_manager.sync_positions(simulated_position=simulated_position)


#%%
order_df = pd.read_excel('order.xlsx')
stock_manager.execute_orders(order_df=order_df)

# %%
