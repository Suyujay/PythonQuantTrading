import requests
from dotenv import load_dotenv
import os

def send_line_message(messages):
    """
    發送 Line 訊息的函數。

    :param messages: 訊息列表，每個訊息為一個字典，包含 type 和 text
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 載入 .env檔案中定義的變數
    load_dotenv(f"{current_dir}/.env")
    # 取得儲存在 .env檔案中 FINLAB API Token
    line_token = os.getenv("LINETOKEN")
    user_id = os.getenv("LINEUSERID")

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_token}"
    }
    payload = {
        "to": user_id,
        "messages": [
        {
            "type": "text",
            "text": f"{messages}"
        },]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code
