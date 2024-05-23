import cv2

from datetime import datetime

# 获取当前时间
now = datetime.now()
str_time = now.strftime("%Y-%m-%d-%H-%M")
str_time = str_time.replace('-','') + '_video.avi'
# # 定义保存视频的格式（MP4）
# fourcc = cv2.VideoWriter_fourcc(*'MP4V')
#
# # 创建VideoWriter对象：保存文件名，编码器，帧率，分辨率
# out = cv2.VideoWriter('output4.mp4', fourcc, 20.0, (1280,720))

fourcc = cv2.VideoWriter_fourcc(*'XVID')
w, h = 1920,1080
out = cv2.VideoWriter(str_time, fourcc, 20.0, (w, h), True)


# 海康相机的RTSP URL，需要替换为你相机的实际信息。
# 这通常包含用户名、密码、IP地址以及流的访问路径。
# 注意：下面的URL只是一个示例格式，你的相机RTSP URL可能有所不同，请参考相机文档获得正确的URL格式。
rtsp_url = 'rtsp://admin:Password@192.168.1.65/Streaming/Channels/1'

# 使用OpenCV的VideoCapture方法来获取视频流
cap = cv2.VideoCapture(rtsp_url)

# 检查视频是否成功打开
if not cap.isOpened():
    print("无法打开视频流或文件")
    exit()

while True:
    # 逐帧捕捉
    ret, frame = cap.read()
    # 如果正确读取帧，ret为True
    if not ret:
        print("无法接收帧（流结束？）。退出 ...")
        break

    # 实时展示帧
    out.write(frame)
    cv2.imshow('frame', frame)

    # 按'q'键退出循环
    if cv2.waitKey(1) == ord('q'):
        break

out.release()
# 完成后释放捕捉器
cap.release()
# 关闭所有OpenCV窗口
cv2.destroyAllWindows()