# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# from io import BytesIO
# from PIL import Image
# import base64
# from API.models.detection_module import yolo_model
# model =yolo_model()
# import cv2
#
# app = FastAPI()
# @app.post("/predict")
# def predict(file: UploadFile = File(...)):
#     # 读取上传的图像文件数据
#     file_bytes = file.file.read()
#
#     # 使用 PIL 打开图像
#     image = Image.open(BytesIO(file_bytes))
#     result_dic = model.process(image)
#     _, img_bytes = cv2.imencode(".jpg", result_dic["Image"], [cv2.IMWRITE_JPEG_QUALITY, 90])
#     result_dic["Image"] = base64.b64encode(img_bytes).decode('utf-8')
#     return JSONResponse(content=result_dic)
#
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO
import base64
import cv2
from API.models.detection_module import yolo_model

app = FastAPI()
model = yolo_model()


@app.post("/predict")
async def predict(image_data: dict = Body(...)):  # 接收Base64 JSON
    try:
        # 解码Base64图像
        image_bytes = base64.b64decode(image_data["image_base64"])
        image = Image.open(BytesIO(image_bytes))

        # 处理图像
        result_dic = model.process(image)

        # 编码结果图像为Base64
        _, img_bytes = cv2.imencode(".jpg", result_dic["Image"], [cv2.IMWRITE_JPEG_QUALITY, 90])
        result_dic["Image"] = base64.b64encode(img_bytes).decode('utf-8')

        return JSONResponse(content=result_dic)

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=400
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)