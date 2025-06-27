from ultralytics import YOLO

# 1. 加载本地模型
model = YOLO('best.pt')

# 2. 推理并保存标注后的视频
#    - source: 输入视频路径
#    - save: 是否保存，可选值 True/False
#    - save_dir: 保存目录
#    - name: 输出子文件夹名称
#    - show: 是否弹窗预览（一般设为 False）
model.predict(
    source='test.avi',
    save=True,
    save_dir='outputs',
    name='det_video',
    show=False
)

print("检测完成，结果保存在：outputs/det_video")
