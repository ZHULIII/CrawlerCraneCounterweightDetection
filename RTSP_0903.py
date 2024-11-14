import cv2

# RTSP URL
rtsp_url = "rtsp://admin:zlzk123456@192.168.1.48:554/Streaming/channels/101"
# rtsp_url = "rtsp://admin:zlzk123456@192.168.8.12:554/Streaming/channels/101"

# 创建VideoCapture对象
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    # 读取帧
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    # 显示帧
    cv2.imshow('RTSP Stream', frame)

    # 按'q'键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放VideoCapture对象并关闭窗口
cap.release()
cv2.destroyAllWindows()