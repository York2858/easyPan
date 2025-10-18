import requests
from loguru import logger

def send_request(method, url, headers=None, data=None, json=None, files=None):
    print(f"\n=== 请求信息 ===")
    print(f"URL: {url}")
    print(f"Method: {method}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    print(f"Json: {json}")
    res = requests.request(method=method, url=url, headers=headers, data=data, json=json, files=files)
    print(f"=== 响应信息 ===")
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text}")
    return res