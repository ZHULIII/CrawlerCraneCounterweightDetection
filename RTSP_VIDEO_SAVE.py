import cv2

# RTSP URL
#rtsp_url = "rtsp://admin:zlzk123456@192.168.1.48:554/Streaming/channels/101"
rtsp_url = "rtsp://admin:zlzk123456@192.168.8.12:554/Streaming/channels/101"

# 创建VideoCapture对象
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# 获取视频的宽度和高度
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 定义视频编码器和输出文件名
from datetime import datetime

# 获取当前时间
now = datetime.now()
str_time = now.strftime("%Y-%m-%d-%H-%M")
str_time = str_time.replace('-','') + '_video.avi'

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(str_time, fourcc, 20.0, (width, height))

while True:
    # 读取帧
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    # 写入帧到输出文件
    out.write(frame)

    # 显示帧
    cv2.imshow('RTSP Stream', frame)

    # 按'q'键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放VideoCapture对象并关闭窗口
cap.release()
out.release()
cv2.destroyAllWindows()