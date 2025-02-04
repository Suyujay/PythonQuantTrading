"""
1.如果還沒有安裝 finlab 套件，先在終端機執行「pip install finlab」
2.在終端機執行「cd BookCodeV1資料夾位置」切換到「BookCodeV1」資料夾下
3.在終端機中輸入「python Chapter1/1-1/get_financial_data_from_finlab.py」來執行程式
"""

# 載入需要的套件
import os

import finlab
from dotenv import load_dotenv
from finlab import data

# 載入.env檔案中定義的變數
load_dotenv("Chapter1/.env")

# 取得儲存在.env檔案中 FINLAB API Token
FINLABTOKEN = os.getenv("FINLABTOKEN")
# 使用 API Token 登入 FinLab 量化平台
finlab.login(api_token=FINLABTOKEN)

# 以取得「現金及約當現金」的財務報表數據為例
# 對應的使用方法為 [financial_statement:現金及約當現金]
# 使用 .deadline() 將索引從季別「年度-季度」格式轉為財報截止日「yyyy-mm-dd」
# 公司財報截止日對應為：{'Q1':'5-15','Q2':'8-14','Q3':'11-14','Q4':'3-31'}
df = data.get("financial_statement:現金及約當現金").deadline()
print("取得「現金及約當現金」的財務報表數據:")
print(df)
print("-----------------------------")

# 顯示某五間公司最後五季的資料
print(df.iloc[-5:, -5:])
