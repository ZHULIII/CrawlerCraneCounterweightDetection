from ultralytics import YOLO

# Load the YOLOv8 model
model = YOLO('utils\\models\\best.pt')
# Export the model to TensorRT format
# model.export(format='engine',half=False)  # creates 'yolov8n.engine'

# Export the model to TensorRT format
model.export(format='onnx',half=False)  # creates 'best.onnx'

# # Load the exported TensorRT model
# tensorrt_model = YOLO('utils/best.engine',task='segment')

# # Run inference
# results = tensorrt_model('video_data\ch2_20240307_163734.avi')