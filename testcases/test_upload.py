import pytest
import yaml
import requests
import os
import math
import hashlib
import allure

# 读取配置文件
with open("config/config.yaml", encoding="utf-8") as f:
    conf = yaml.safe_load(f)
base_url = conf["base_url"]

def calc_md5(file_path, chunk_size=1024 * 1024 * 5):
    """计算文件 MD5（与前端 SparkMD5 一致）"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()

@allure.feature("文件上传接口")
class TestFileUpload:
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

    # def test_get_file_list(self):
    #     """获取文件列表"""
    #     url = f"{base_url}/file/loadDataList"
    #     data = {
    #         "category": "all",
    #         "filePid": "0",
    #         "pageNo": "1",
    #         "pageSize": "15"
    #     }

    #     res = self.session.post(url, data=data)
    #     print("文件列表响应:", res.text)

    #     assert res.status_code == 200
    #     json_data = res.json()
    #     assert json_data["code"] == 200, f"接口返回错误: {json_data}"
    #     print("成功获取文件列表")

    #     if json_data["data"]["totalCount"] > 0:
    #         first_file = json_data["data"]["list"][0]
    #         print("首个文件名:", first_file["fileName"])
    

    
    @pytest.mark.parametrize("file_path", [
        r"C:\Users\l2858\Desktop\简历\李佳鑫简历.pdf",  # 换成你自己的测试文件路径
    ])
    @allure.story("分片上传 + 秒传验证")
    def test_upload_file(self, file_path):
        """完整测试：上传 -> 秒传"""
        file_name = os.path.basename(file_path)
        file_pid = "0"
        chunk_size = 1024 * 1024 * 5  # 5MB
        file_size = os.path.getsize(file_path)
        chunks = math.ceil(file_size / chunk_size)
        file_md5 = calc_md5(file_path)

        allure.dynamic.title(f"文件上传测试: {file_name}")
        allure.attach(
            f"文件: {file_name}\n大小: {file_size}\n分片数: {chunks}\nMD5: {file_md5}",
            "上传文件信息",
            allure.attachment_type.TEXT
        )

        # === 第一次上传 ===
        upload_status = self.upload_file_chunks(file_path, file_name, file_pid, file_md5, chunks, chunk_size)
        assert upload_status == "upload_finish", f"第一次上传未完成：{upload_status}"

        # === 第二次上传，测试秒传 ===
        with allure.step("验证秒传逻辑"):
            status = self.upload_file_chunks(file_path, file_name, file_pid, file_md5, chunks, chunk_size)
            assert status == "upload_seconds", f"秒传验证失败，返回状态：{status}"

    # 内部上传函数
    def upload_file_chunks(self, file_path, file_name, file_pid, file_md5, chunks, chunk_size):
        """分片上传核心逻辑"""
        url = f"{base_url}/file/uploadFile"
        file_id = None

        with open(file_path, "rb") as f:
            for i in range(chunks):
                start = i * chunk_size
                f.seek(start)
                chunk = f.read(chunk_size)
                files = {"file": (file_name, chunk)}
                data = {
                    "fileId": file_id or "",
                    "fileName": file_name,
                    "filePid": file_pid,
                    "fileMd5": file_md5,
                    "chunkIndex": i,
                    "chunks": chunks,
                }

                with allure.step(f"上传分片 {i + 1}/{chunks}"):
                    res = self.session.post(url, data=data, files=files)
                    assert res.status_code == 200
                    res_json = res.json()
                    allure.attach(str(res_json), name=f"分片{i+1}响应", attachment_type=allure.attachment_type.JSON)

                    assert res_json["code"] == 200, f"接口错误：{res_json}"
                    result = res_json["data"]
                    status = result.get("status")
                    file_id = result.get("fileId", file_id)

                    if status == "uploading":
                        print(f"分片 {i+1}/{chunks} 上传中")
                        continue
                    elif status in ("upload_finish", "upload_seconds"):
                        print(f"上传完成，状态：{status}")
                        return status
        return status