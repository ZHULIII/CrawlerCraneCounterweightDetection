# import requests
#
# # 服务器地址和接口路径
# url = "http://localhost:8001/predict"
#
# # 图片文件路径（请根据实际情况替换图片路径）
# image_path = "test.jpg"
#
# with open(image_path, "rb") as image_file:
#     # 构造上传文件的数据字典
#     files = {"file": image_file}
#     response = requests.post(url, files=files)
#
# # 打印返回的结果
# print("Response status code:", response.status_code)
# print("Response content:", response.json())
import requests
import base64
import json
import os
# 服务器地址
url = "http://localhost:8001/predict"

# 读取图片并编码为Base64
with open(os.path.dirname(os.path.abspath(__file__))+"/R-C.jpg", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

# 构造请求数据
payload = {
    "image_base64": image_base64,
    "other_metadata": "optional_data"  # 可添加其他元数据
}

# 发送请求（使用json参数自动序列化）
response = requests.post(
    url,
    json=payload,  # 自动设置Content-Type为application/json
    headers={"Content-Type": "application/json"}
)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print("Detection Results:", result)

    # 如果需要解码结果图像
    if "Image" in result:
        image_data = base64.b64decode(result["Image"])
        with open("result.jpg", "wb") as f:
            f.write(image_data)
        print("Saved result image to result.jpg")
else:
    print("Error:", response.status_code, response.text)
