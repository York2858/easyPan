import pytest
import requests
import yaml

# 读取配置文件
with open("config/config.yaml", encoding="utf-8") as f:
    conf = yaml.safe_load(f)
base_url = conf["base_url"]

@pytest.fixture(scope="session")
def login_session():
    """会话级登录 fixture，只执行一次"""
    session = requests.Session()
    url = f"{base_url}/login"
    payload = {
        "email": "2858796330@qq.com",
        "password": "2303de05fb0b3646775945cad78ec664",
        "checkCode": "testa"
    }
    res = session.post(url, data=payload)
    assert res.status_code == 200
    assert res.json()["code"] == 200
    print("登录成功，Token:", session.cookies.get_dict())
    return session
