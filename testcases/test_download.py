import pytest
import requests
import yaml
import os
import hashlib
import allure

# === 读取配置文件 ===
with open("config/config.yaml", encoding="utf-8") as f:
    conf = yaml.safe_load(f)
base_url = conf["base_url"]


def md5sum(file_path):
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


@allure.feature("文件下载流程自动化测试")
class TestFileDownloadFlow:
    """文件下载完整流程"""

    # 类属性共享
    session = None
    file_id = None
    file_name = None
    download_token = None

    @classmethod
    def setup_class(cls):
        """登录并保持会话"""
        cls.session = requests.Session()
        login_url = f"{base_url}/login"
        payload = {
            "email": "2858796330@qq.com",
            "password": "2303de05fb0b3646775945cad78ec664",
            "checkCode": "testa"
        }
        res = cls.session.post(login_url, data=payload)
        assert res.status_code == 200
        res_json = res.json()
        assert res_json["code"] == 200
        print("✅ 登录成功，Cookie:", cls.session.cookies.get_dict())

    @allure.story("1. 获取文件列表")
    def test_get_file_list(self):
        """获取文件列表，提取文件ID"""
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
        assert json_data["code"] == 200
        assert json_data["data"]["totalCount"] > 0, "当前用户网盘为空！"

        # 取第一个文件ID
        TestFileDownloadFlow.file_id = json_data["data"]["list"][0]["fileId"]
        TestFileDownloadFlow.file_name = json_data["data"]["list"][0]["fileName"]
        print(f"✅ 获取文件ID: {self.file_id} 文件名: {self.file_name}")

    @allure.story("2. 创建下载链接")
    def test_create_download_url(self):
        """创建文件下载URL"""
        assert TestFileDownloadFlow.file_id is not None, "文件ID为空，请先运行 test_get_file_list"
        url = f"{base_url}/file/createDownloadUrl/{TestFileDownloadFlow.file_id}"
        res = self.session.get(url)
        print("创建下载URL响应:", res.text)
        assert res.status_code == 200

        json_data = res.json()
        assert json_data["code"] == 200
        assert "data" in json_data

        # data 返回 token
        if isinstance(json_data["data"], str):
            TestFileDownloadFlow.download_token = json_data["data"]
        else:
            TestFileDownloadFlow.download_token = json_data["data"]["downloadUrl"]

        print(f"✅ 获取下载token: {self.download_token}")

    @allure.story("3. 下载文件并验证内容")
    def test_download_file(self):
        """使用下载链接下载文件并验证"""
        assert TestFileDownloadFlow.download_token is not None, "下载 token 为空，请先运行 test_create_download_url"
        download_url = f"{base_url}/file/download/{TestFileDownloadFlow.download_token}"
        print(f"开始下载文件: {download_url}")

        res = self.session.get(download_url, stream=True)
        assert res.status_code == 200, f"下载失败，状态码：{res.status_code}"

        # 保存文件
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        local_path = os.path.join(download_dir, TestFileDownloadFlow.file_name)
        with open(local_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        # 验证文件大小
        file_size = os.path.getsize(local_path)
        print(f"✅ 下载完成，文件大小：{file_size} bytes")
        assert file_size > 0, "下载文件为空！"

        # MD5 校验
        file_md5 = md5sum(local_path)
        print(f"文件 MD5: {file_md5}")

        allure.attach(local_path, "下载文件路径")
        allure.attach(file_md5, "文件MD5", allure.attachment_type.TEXT)
