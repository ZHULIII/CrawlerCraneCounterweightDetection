import cv2
from datetime import datetime

# 获取当前时间
now = datetime.now()
str_time = now.strftime("%Y-%m-%d-%H-%M")
str_time = str_time.replace('-','') + 'testwrite.avi'
# # 定义保存视频的格式（MP4）
# fourcc = cv2.VideoWriter_fourcc(*'MP4V')
#
# # 创建VideoWriter对象：保存文件名，编码器，帧率，分辨率
# out = cv2.VideoWriter('output4.mp4', fourcc, 20.0, (1280,720))

fourcc = cv2.VideoWriter_fourcc(*'XVID')
w, h = 1920,1080
out = cv2.VideoWriter(str_time, fourcc, 20.0, (w, h), True)

# 接入相机（0是第一个相机，如果有多个相机，可以尝试1, 2, ...）s
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
while(cap.isOpened()):
    # 读取帧q
    ret, frame = cap.read()
    if ret == True:
        # 通过VideoWriter对象写帧到文件
        out.write(frame)

        # 显示帧
        cv2.imshow('frame', frame)
        print('',frame.shape)
        # 按'q'退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# 释放摄像头资源
cap.release()

# 释放和关闭VideoWriter对象
out.release()

# 关闭所有OpenCV窗口
cv2.destroyAllWindows()