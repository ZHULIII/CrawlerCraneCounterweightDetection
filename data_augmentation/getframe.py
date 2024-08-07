import cv2
import os
import argparse

def extract_frames(video_path, output_dir, num_frames, index):
    # 创建输出目录
    count =1
    origin_output_dir = output_dir
    while 1:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            break
        output_dir = origin_output_dir + str(count)
        count +=1

    # 打开视频文件
    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        print("无法打开视频文件！")
        return
    print("视频已打开")

    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    print("视频总帧数:", total_frames)

    # 确定每个间隔多少帧取一次
    frame_interval = total_frames // num_frames

    # 初始化计数器
    frame_count = 0
    saved_count = 0

    # 逐帧读取视频
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # 每隔frame_interval帧保存一帧
        if frame_count % frame_interval == 0:
            output_path = os.path.join(output_dir, f"frame_{index}_{saved_count}.jpg")
            cv2.imwrite(output_path, frame)
            saved_count += 1

        frame_count += 1

    # 释放资源
    video_capture.release()
    print(f"成功保存了 {saved_count} 张帧.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract frames from a video')
    parser.add_argument('--video_path', type=str, help='视频文件路径')
    parser.add_argument('--num_frames', type=int, help='要提取的帧数')
    parser.add_argument('--output_dir', type=str, default="output_frames",help='输出帧的保存目录',required=False)
    args = parser.parse_args()

    # 提取帧
    # extract_frames(args.video_path, args.output_dir, args.num_frames)
    extract_frames("C://Users//24536\Desktop\weight_data//0706//0//output.avi", "C://Users//24536//Desktop//weight_data//0706//1", 30,4)