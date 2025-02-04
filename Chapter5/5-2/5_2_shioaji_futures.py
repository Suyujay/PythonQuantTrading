#%%
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
    ca_passwd="",
    person_id="",
)

#%%
#獲取持倉
positions = api.list_positions(api.futopt_account)
position_df = pd.DataFrame(p.__dict__ for p in positions)
print(position_df)
#%%
# 所有契約
print(api.Contracts.Futures)

#%%
print(api.Contracts.Futures.TXF)
#%%契約
contract_TXF = getattr(api.Contracts.Futures.TXF, 
                       sorted([x for x in dir(api.Contracts.Futures.TXF) 
                               if x.startswith('TXF')])[-2])
print(contract_TXF)
#%%
# 台指近全
contract_txf = api.Contracts.Futures.TXF.TXFR1
print(contract_txf)

#%%
#獲取行情資料
kbars = api.kbars(
    contract=contract_txf, 
    start="2023-01-01", 
    end="2024-12-10", 
)
price_data = pd.DataFrame({**kbars})
price_data.ts = pd.to_datetime(price_data.ts)
print(price_data)
#%%
# 歷史行情儲存成 30 分 K 以利回測
price_data = price_data.rename(columns={'ts':'Date'})
price_data = price_data.set_index('Date')
price_data = price_data.between_time('08:45', '13:45')

# 早上8:45 ~ 13:45的資料做resample，並使用offset
price_data = price_data.resample(
    '30min', closed='right', label='right', offset='15min').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()
price_data.to_csv('TXF_30.csv')

#%%
#獲取行情資料
ticks = api.ticks(
    contract=contract_txf, 
    date='2024-12-11'
    )
price_data = pd.DataFrame({**ticks})
price_data.ts = pd.to_datetime(price_data.ts)
print(price_data)

#%% 
# # 台指期市價單 Buy
order_txf = api.Order(
        action=sj.constant.Action.Buy,
        price=int(price_data['Close'].tolist()[-1]),
        quantity=1,
        price_type=sj.constant.FuturesPriceType.MKT,
        order_type=sj.constant.OrderType.IOC,
        octype=sj.constant.FuturesOCType.Auto,
        account=api.futopt_account
    )
trade_mxf = api.place_order(contract_txf, order_txf)

#%% 
# 台指期市價單 Sell 
order_txf = api.Order(
        action=sj.constant.Action.Sell,
        price=int(price_data['Close'].tolist()[-1]),
        quantity=1,
        price_type=sj.constant.FuturesPriceType.MKT,
        order_type=sj.constant.OrderType.IOC,
        octype=sj.constant.FuturesOCType.Auto,
        account=api.futopt_account
    )
trade_mxf = api.place_order(contract_txf, order_txf)

#%% 
# 台指期 Limit 單 Buy 
order_txf = api.Order(
        action=sj.constant.Action.Buy,
        price=int(price_data['Close'].tolist()[-1]),
        quantity=1,
        price_type=sj.constant.FuturesPriceType.LMT,
        order_type=sj.constant.OrderType.ROD,
        octype=sj.constant.FuturesOCType.Auto,
        account=api.futopt_account
    )
trade_mxf = api.place_order(contract_txf, order_txf)

#%%
# 台指期 Limit 單 Sell 
order_txf = api.Order(
        action=sj.constant.Action.Sell,
        price=int(price_data['Close'].tolist()[-1]),
        quantity=1,
        price_type=sj.constant.FuturesPriceType.LMT,
        order_type=sj.constant.OrderType.ROD,
        octype=sj.constant.FuturesOCType.Auto,
        account=api.futopt_account
    )
trade_mxf = api.place_order(contract_txf, order_txf)
# %%
