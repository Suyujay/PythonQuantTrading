import requests

url = "https://api.line.me/v2/bot/message/push"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer FoD9QnEO9hL5bk0GBHv6Emc3LTSVQ8GPEva/tnFKi+1x4pehBqdDsLBvB8itw/paFmjqx/My7N2S2GSGVbS3Vq+QU//BoBtlxY8kiVA/Rokhl0vIvJot/TFC3+no7gXu1+zTsj55Dxtq8IZZk4ockAdB04t89/1O/w1cDnyilFU="  # 替換成你的 Channel Access Token
}

payload = {
    "to": "U72bb16001e1832fcbe76c64bf7397d63",  
    "messages": [
        {
            "type": "text",
            "text": "Hello, world1"
        },
        {
            "type": "text",
            "text": "Hello, world2"
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)

# 檢查回應
if response.status_code == 200:
    print("Message sent successfully")
else:
    print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")


# # 獲取好友 id
url = "https://api.line.me/v2/bot/followers/ids"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer FoD9QnEO9hL5bk0GBHv6Emc3LTSVQ8GPEva/tnFKi+1x4pehBqdDsLBvB8itw/paFmjqx/My7N2S2GSGVbS3Vq+QU//BoBtlxY8kiVA/Rokhl0vIvJot/TFC3+no7gXu1+zTsj55Dxtq8IZZk4ockAdB04t89/1O/w1cDnyilFU="  # 替換成你的 Channel Access Token
}

response = requests.get(url, headers=headers)

# 檢查回應
if response.status_code == 200:
    print("Message sent successfully")
else:
    print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")