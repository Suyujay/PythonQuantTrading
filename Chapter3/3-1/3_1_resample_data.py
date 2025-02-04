#import套件
import pandas as pd
#讀取分K檔案
x = pd.read_csv('TXF.csv')
print(x)
#為x建立index，供轉換使用
x = x.set_index(pd.DatetimeIndex(x.Date))
#示錯誤的示範-早盤不加參數的 agg
df30 = x.resample('30min').agg({
    'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'
}).dropna()
# 儲存成新的csv檔案
df30.to_csv('TXF_30_Test.csv')

# #%%
#轉換成30分K
#closed='right' =>  8:30  <  x <= 9:00 
#closed='left'  =>   8:30 <= x <  9:00

#label='right' => 8:30+15 - 9:00+15的資料歸屬在9:00
#label='left' => 8:30-9:00的資料歸屬在8:30

# #offset偏移量
# df30 = x.resample('30min',closed='right',label='right',offset='15min').agg({
#     'open':'first','high':'max','low':'min','close':'last','volume':'sum'
# }).dropna()
# #儲存成新的csv檔案
# df30.to_csv('D:\mastertalk\code\TXF_30.csv')


morning_data = x.between_time('08:45', '13:45')
afternoon_data = x.between_time('15:00', '05:00')

# 早上8:45 ~ 13:45的資料做resample，並使用offset
morning_resampled = morning_data.resample(
    '30min', closed='right', label='right', offset='15min').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()
print(morning_resampled)

# 下午15:00 ~ 隔日凌晨3:00的資料做resample，不使用offset
afternoon_resampled = afternoon_data.resample(
    '30min', closed='right', label='right').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()
print(afternoon_resampled)

# 合併早上和下午的resample結果
df30 = pd.concat([morning_resampled, afternoon_resampled]).sort_index()
df30.to_csv('TXF_30.csv')

