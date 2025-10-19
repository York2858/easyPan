import pytest
import yaml
import requests
import allure

# 读取配置文件
with open("config/config.yaml", encoding="utf-8") as f:
    conf = yaml.safe_load(f)
base_url = conf["base_url"]

@allure.feature("获取信息接口")
class TestGetInfo:
    def setup_class(self):
        """登录并保持 session"""
        self.session = requests.Session()
        url = f"{base_url}/login"
        payload = {
            "email": "2858796330@qq.com",
            "password": "2303de05fb0b3646775945cad78ec664",  # 已加密密码
            "checkCode": "testa"
        }
        # 直接用 self.session 发送登录请求
        res = self.session.post(url, data=payload)
        print("登录响应:", res.text)
        assert res.status_code == 200
        assert res.json()["code"] == 200

        # 查看 Cookie 是否保存成功
        print("登录后 Cookie:", self.session.cookies.get_dict())
        assert "satoken" in self.session.cookies.get_dict() or res.headers.get("satoken"), "未检测到登录 Token"

    @allure.story("获取文件列表")
    def test_get_file_list(self):
        """获取文件列表"""
        url = f"{base_url}/file/loadDataList"
        data = {
            "category": "all",
            "filePid": "0",
            "pageNo": "1",
            "pageSize": "15"
        }

        res = self.session.post(url, data=data)
        print("文件列表响应:", res.text)

        assert res.status_code == 200
        json_data = res.json()
        assert json_data["code"] == 200, f"接口返回错误: {json_data}"
        print("成功获取文件列表")

        if json_data["data"]["totalCount"] > 0:
            first_file = json_data["data"]["list"][0]
            print("首个文件名:", first_file["fileName"])