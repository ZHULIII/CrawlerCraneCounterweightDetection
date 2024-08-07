# This Python file uses the following encoding: utf-8

from PySide6.QtGui import QPixmap,QImage
from PySide6.QtCore import Qt, QThread, Signal
import cv2
import time
from ultralytics import YOLO
import numpy as np
from collections import deque, Counter
from knn import knn_classifier
from knn import write_cache_to_log
from datetime import datetime
from numba import jit
import torch
class Stream_Inference(QThread):
    processed_image = Signal(QImage)
    result_info = Signal(int,float,float,float,str)
    def __init__(self,stream_path,weight_path,imgsz,conf,device,weight_sr,weight_character,imgsz_2,conf_2,device_2):
        super().__init__()
        #配重检测
        # 添加日志文件地址
        self.log_dir = "logs/" + datetime.now().strftime("%Y_%m_%d")+ '.txt'
        # 添加logger cache
        self.log_cache = []
        self.log_line_counter = -1
        # 跳帧预测
        self.frame_skip =3

        self.stream_path = stream_path
        self.weight_path = weight_path
        self.weight_character = weight_character
        self.imgsz = imgsz
        self.conf=conf
        self.device=device
        self.model = YOLO(self.weight_path,task='segment')
        self.thread_stop = False
        self.label=True
        self.box = True

        #切片字符检测
        self.sr_model_flag = False
        # self.sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
        # self.sr_model.readModel(weight_sr)
        # self.sr_model.setModel("espcn", 2)
        self.sr_model = None
        self.model_character = YOLO(self.weight_character)
        self.model_character_dic = {0: '10t', 1: '5.1t', 2: '5t', 3: '8.1t'}
        self.imgsz_2 = imgsz_2
        self.conf_2=conf_2
        self.device_2=device_2

        #结果信息
        self.num_weight=5
        self.num_weight_queue = deque(maxlen=5)
        self.total_mass=10.00
        self.total_mass_L=5.00
        self.total_mass_R=5.00
        self.warming_info="安全"

        # 聚类过滤功能阈值
        self._sample_filter_x = 0.2
        self._sample_filter_center = (0.5, 0.55)
        self._gauss_filter = True

    def stop(self):
        self.thread_stop = True

    def sr_model_state(self):
        self.sr_model_flag=True

    def _slice_classify(self, slice_list):
        dic_target = {0:0,1:0,2:0,3:0}
        character_pos=[]
        for slice_img, conf, int_box in slice_list:
            result = self.model_character.predict(slice_img,imgsz=self.imgsz_2,conf=self.conf_2,device=self.device_2)
            inference_number = result[0].boxes.cls.cpu().numpy()
            boxes = result[0].boxes.cpu().numpy().data
            sorted_box_list = sorted(boxes, key=lambda x: x[4], reverse=True)
            char_int_boxes =  np.floor(sorted_box_list).astype(int)
            if len(inference_number) < 1:
                continue
            else:
                #针对单张子图识别出多个类别的情况进行优化，只返回子图中出现次数最多的数字
                unique_nums, counts = np.unique(inference_number, return_counts=True)
                most_frequent_index = np.argmax(counts)
                most_frequent = int(unique_nums[most_frequent_index])
                dic_target[most_frequent] += 1
                int_box[0], int_box[1], int_box[2], int_box[3] = int_box[0]+char_int_boxes[0][0],int_box[1]+char_int_boxes[0][1],int_box[0]+char_int_boxes[0][2],int_box[1]+char_int_boxes[0][3]
                #字符位置
                character_pos.append(int_box)
        # 返回出现次数最多的数字
        return max(dic_target, key=lambda k: dic_target[k]),character_pos

    def _get_image_slice(self):
        #获取原始图像
        original_image = self.result[0].orig_img
        boxes = self.result[0].boxes.cpu().numpy().data
        # 置信度
        conf_list = boxes[:, 4]
        # 对检测框参数进行向下取整
        int_boxes = np.floor(boxes).astype(int)
        img_list = []
        for i in range(int_boxes.shape[0]):
            x1, y1, x2, y2 = int_boxes[i][0], int_boxes[i][1], int_boxes[i][2], int_boxes[i][3]
            img_i = original_image[y1:y2 + 1, x1:x2 + 1]
            # 如果需要进行超分辨里增强的话，则调用sr_model完成上采样操作（默认放大因子为2）
            if self.sr_model_flag:
                img_i = self.sr_model.upsample(img_i)
            img_list.append((img_i,conf_list[i],int_boxes[i]))
        return img_list

    def _sample_distance_calculation(self,current_point, keypoint_list, x_max_value):
        x_min_threshold, x_max_threshold = x_max_value*self._sample_filter_x, x_max_value*(1-self._sample_filter_x)
        target_x = (current_point[0] +current_point[2])/2
        target_y = (current_point[1] +current_point[3])/2
        min_distance = 1000000
        flag = 0
        for p in range(len(keypoint_list)):
            # 欧式距离计算
            d = ((keypoint_list[p][0] - target_x) ** 2 + (keypoint_list[p][1]-target_y)**2) ** 0.5
            if min_distance > d:
                min_distance, flag= d, p
        # 返回距离哪个点最近
        if flag == 4:
            return True
        else:
            if target_x < x_min_threshold or target_x > x_max_threshold:
                return False
        return True


    def _sample_filter(self):
        if not self._gauss_filter:
            return
        try:
            boxes = self.result[0].boxes.cpu().numpy().data
        # 如果没有检测出识别框，无法取得boxes数据
        except:
            return
        int_boxes = np.floor(boxes).astype(int)
        y_max, x_max = self.result[0].orig_shape[0],  self.result[0].orig_shape[1]
        center_point_x, center_point_y = int(x_max*self._sample_filter_center[0]), int(y_max*self._sample_filter_center[1])
        keypoint_list = [(0,0), (0, y_max), (x_max, 0), (x_max, y_max), (center_point_x, center_point_y)]
        delete_index = []
        for i in range(int_boxes.shape[0]):
            # 过滤出target，需要满足两个条件，1.目标点在距离四个角点更近 2.目标中心点位于图像左右两侧阈值
            current_point = int_boxes[i]
            if not self._sample_distance_calculation(current_point, keypoint_list, x_max):
                # 需要删除的目标框的index
                delete_index.append(i)
        if len(delete_index) > 0:
            all_list = [i for i in range(int_boxes.shape[0])]
            # select_index = torch.tensor([sorted([item for item in all_list if item not in delete_index])],device=self.device)
            select_index = sorted([item for item in all_list if item not in delete_index])
            self.result[0].boxes.data = self.result[0].boxes.data[select_index, :]
            # self.result[0].boxes.xywh = self.result[0].boxes.xywh[select_index, :]
            # self.result[0].boxes.xywhn = self.result[0].boxes.xywhn[select_index, :]
            # self.result[0].boxes.xyxy = self.result[0].boxes.xyxy[select_index, :]
            # self.result[0].boxes.xyxyn = self.result[0].boxes.xyxyn[select_index, :]
        return

    @jit(nopython=True)
    def write_cache_to_log(self):
        try:
            with open(self.log_dir, 'a') as log_file:
                for log_entry in self.log_cache:
                    log_file.write(log_entry + '\n')
                self.log_cache = []  # 清空缓存
        except IOError as e:
            print(f"写入日志时发生错误：{e}")


    def run(self):
        cap = cv2.VideoCapture(self.stream_path)
        #未捕获video
        if not cap.isOpened():
            self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info = 0,0,0,0,"视频流中断，请检查网络相机连接情况"
            self.result_info.emit(self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info)
            cap.release()
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        delta_time=1000/fps
        time1= time.time()
        count=0
        while cap.isOpened() and not self.thread_stop:
            start_time = time.time()
            ret, frame = cap.read()
            if ret:
                if count==0:
                    # print("start model predict")
                    self.result = self.model(frame,imgsz=self.imgsz,conf=self.conf,device=self.device)
                    self._sample_filter()
                    # 通过预测狂和原始图像数据得到切片图像，通过对切片图像完成超分辨率增强后输出结果 [(图像切片1，置信度1),(图像切片2， 置信度2).....]
                    slice_result = self._get_image_slice()
                    classify_number,character_pos = self._slice_classify(slice_result)
                    annotated_image = self.result[0].plot(conf=True,line_width=2,font_size=None,font="Arial.ttf",pil=False,img=None,im_gpu=None,kpt_radius=5,
                                kpt_line=True,labels=self.label,boxes=self.box,masks=False,probs=True,show=False,save=False,filename=None)
                    for box in character_pos:
                        cv2.rectangle(annotated_image, (box[0], box[1]), (box[2], box[3]),  color=(0,0,255), thickness=2)
                    rgb_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qimage = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    # 将检测结果添加到队列中
                    self.num_weight_queue.append(len(self.result[0].boxes))
                    # 获取队列中元素的统计信息
                    counter = Counter(self.num_weight_queue)
                    # 获取出现次数最多的元素（众数）
                    self.num_weight = counter.most_common(1)[0][0]
                    # 计算左右两边配重块数和重量
                    boxes_number = self.result[0].boxes.cpu().numpy().data
                    int_boxes_number = np.floor(boxes_number).astype(int)
                    self.weight_left_number, self.weight_right_number = knn_classifier(int_boxes_number)
                    self.total_mass_L = self.weight_left_number * float(eval(self.model_character_dic[classify_number][0:-1]))
                    self.total_mass_R = self.weight_right_number * float(eval(self.model_character_dic[classify_number][0:-1]))
                    # 计算完之后对左右数量置为0，避免带入缓存误差
                    self.weight_left_number, self.weight_right_number = 0, 0

                    self.processed_image.emit(qimage)
                    self.total_mass = self.num_weight * float(eval(self.model_character_dic[classify_number][0:-1]))
                    self.log_line_counter += 1
                    if self.log_line_counter % 100 == 0:
                        input_str = datetime.now().strftime("%Y_%m_%d_%H:%M:%S") + " total weight:" + str(
                            self.num_weight) + " total mass:" + str(self.total_mass) + " left mass:" + str(
                            self.total_mass_L) + " right mass:" + str(self.total_mass_R)
                        self.log_cache.append(input_str)
                        write_cache_to_log(self.log_dir, self.log_cache)
                        self.log_cache = []
                    # else:
                    #     input_str = datetime.now().strftime("%Y_%m_%d_%H:%M:%S") + " total weight:" + str(self.num_weight) + " total mass:" + str(self.total_mass) + " left mass:" + str(self.total_mass_L) + " right mass:" + str(self.total_mass_R)
                    #     self.log_cache.append(input_str)
                    self.result_info.emit(self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info)
                count = (count+1) % self.frame_skip
            else:
                break
            end_time = time.time()
            processing_time = (end_time-start_time)*1000
            print(processing_time)
            if processing_time>delta_time:
                continue
            else:
                cv2.waitKey(int(delta_time-processing_time))
        #中途中断
        if not cap.isOpened():
            self.warming_info = "视频流中断，请检查网络相机连接情况"
            self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R = 0,0,0,0
            self.result_info.emit(self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info)
        print((time.time()-time1)*1000)
        cap.release()
    def run_function(self):
        cap = cv2.VideoCapture(self.stream_path)
        #未捕获video
        if not cap.isOpened():
            self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info = 0,0,0,0,"视频流中断，请检查网络相机连接情况"
            self.result_info.emit(self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info)
            cap.release()
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        delta_time=1000/fps
        time1= time.time()
        count=0
        while cap.isOpened() and not self.thread_stop:
            start_time = time.time()
            ret, frame = cap.read()
            if ret:
                if count==0:
                    self.result = self.model(frame,imgsz=self.imgsz,conf=self.conf,device=self.device)
                    # print(1)
                    # 通过预测狂和原始图像数据得到切片图像，通过对切片图像完成超分辨率增强后输出结果 [(图像切片1，置信度1),(图像切片2， 置信度2).....]
                    slice_result = self._get_image_slice()
                    classify_number,character_pos = self._slice_classify(slice_result)
                    annotated_image = self.result[0].plot(conf=True,line_width=2,font_size=None,font="Arial.ttf",pil=False,img=None,im_gpu=None,kpt_radius=5,
                                kpt_line=True,labels=self.label,boxes=self.box,masks=False,probs=True,show=False,save=False,filename=None)
                    for box in character_pos:
                        cv2.rectangle(annotated_image, (box[0], box[1]), (box[2], box[3]),  color=(0,0,255), thickness=2)
                    rgb_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qimage = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    # 将检测结果添加到队列中
                    self.num_weight_queue.append(len(self.result[0].boxes))
                    # 获取队列中元素的统计信息
                    counter = Counter(self.num_weight_queue)
                    # 获取出现次数最多的元素（众数）
                    self.num_weight = counter.most_common(1)[0][0]
                    # 计算左右两边配重块数和重量
                    boxes_number = self.result[0].boxes.cpu().numpy().data
                    int_boxes_number = np.floor(boxes_number).astype(int)
                    self.weight_left_number, self.weight_right_number = knn_classifier(int_boxes_number)
                    self.total_mass_L = self.weight_left_number * float(eval(self.model_character_dic[classify_number][0:-1]))
                    self.total_mass_R = self.weight_right_number * float(eval(self.model_character_dic[classify_number][0:-1]))
                    # 计算完之后对左右数量置为0，避免带入缓存误差
                    self.weight_left_number, self.weight_right_number = 0, 0

                    self.processed_image.emit(qimage)
                    self.total_mass = self.num_weight * float(eval(self.model_character_dic[classify_number][0:-1]))
                    self.result_info.emit(self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info)
                count = (count+1)%3
            else:
                break
            end_time = time.time()
            processing_time = (end_time-start_time)*1000
            print(processing_time)
            if processing_time>delta_time:
                continue
            else:
                cv2.waitKey(int(delta_time-processing_time))
        #中途中断
        if not cap.isOpened():
            self.warming_info = "视频流中断，请检查网络相机连接情况"
            self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R = 0,0,0,0
            self.result_info.emit(self.num_weight,self.total_mass,self.total_mass_L,self.total_mass_R,self.warming_info)
        print((time.time()-time1)*1000)
        cap.release()