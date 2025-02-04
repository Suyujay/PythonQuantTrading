"""
1.如果還沒有安裝 dotenv 套件，先在終端機執行「pip install python-dotenv」
2.在終端機執行「cd BookCodeV1資料夾位置」切換到「BookCodeV1」資料夾下
3.在 BookCodeV1/Chapter1/1-1/ 資料夾下建立 .env檔案
4.在終端機中輸入「python Chapter1/1-1/load_dotenv.py」來執行程式
"""

# 載入需要的套件
import os

from dotenv import load_dotenv

# 載入 .env檔案中定義的變數
load_dotenv("Chapter1/1-1/.env")

# 取得儲存在 .env檔案中 TOKEN1 數值並顯示
TOKEN1 = os.getenv("TOKEN1")
print(f"TOKEN1: {TOKEN1}")  # TOKEN1: 123

# 取得儲存在 .env檔案中 TOKEN2 數值並顯示
TOKEN2 = os.getenv("TOKEN2")
print(f"TOKEN2: {TOKEN2}")  # TOKEN2: 456
