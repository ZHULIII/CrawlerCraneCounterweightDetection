import cv2

# 打开视频捕获设备，0通常是指内置摄像头，外接USB摄像头可能是1或更高的数字
# 你可能需要尝试不同的数字，以找到对应你的USB相机的正确编号
cap = cv2.VideoCapture(1)

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

width, height = 1280, 720
# width, height = 640, 480
# width, height = 3840, 2160
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
while True:
    # 逐帧捕获
    ret, frame = cap.read()

    # 如果正确读取帧，ret为True
    if not ret:
        print("无法接收帧流。正在退出...")
        break

    # 我们在帧上操作
    # 这里简单地显示了帧，也可以做其他操作如图像处理
    cv2.imshow('frame', frame)
    s = str(width)+"_"+str(height)+'saved_image2.png'
    cv2.imwrite(s, frame)
    break

    # 按下'q'键退出循环
    if cv2.waitKey(1) == ord('q'):
        break

# 当一切完成后，释放捕获
cap.release()
cv2.destroyAllWindows()