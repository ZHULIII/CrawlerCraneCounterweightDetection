# 完成模型读取和推理，仅包含模型加载和推理
from ultralytics import YOLO
import torch

import numpy as np
import cv2
import matplotlib.pyplot as plt
from collections import deque, Counter
from API.models.knn import knn_classifier
import os
import json
def read_params(path='params.txt'):
    with open(path, "r", encoding="utf-8") as f:
        params = json.load(f)
    return params

def show_image(image):
    # 显示图像
    plt.figure(figsize=(10, 8))  # 设置画布大小
    plt.imshow(image)
    plt.axis('off')  # 关闭坐标轴
    plt.title("YOLOv8 Detection Results")  # 添加标题（可选）
    plt.show()


class yolo_model:
    def __init__(self,params_path=None):
        # 读取本地参数文档
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.params = read_params(self.current_path+'/params.txt')
        # 读取本地推理所需参数
        self.model_path = self.current_path+ '/' + self.params['yolo_model_path']
        self.imgsz = self.params['yolo_image_size']
        self.conf = self.params['yolo_conf']

        self.log_path = self.current_path+ '/' + self.params['yolo_detection_log']
        self.yolo_model = YOLO(self.model_path,task='segment')

        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            print("========USE YOLO IN GPU==========")
        else:
            self.device = torch.device("cpu")
            print("********USE YOLO IN CPU**********")

        # 后处理参数
        self._gauss_filter = False
        if 'gauss_filter' in self.params.keys():
            self._gauss_filter = eval(self.params['gauss_filter'])


        # 聚类过滤功能阈值
        self._sample_filter_x = 0.2
        self._sample_filter_center = (0.5, 0.55)
        #self._gauss_filter = False

        #超分辨里增强
        self.sr_model_flag = False
        #数字识别分类
        self.imgsz_2=640
        self.conf_2=0.5
        self.model_character_path = self.current_path+ '/' + self.params['model_character_path']
        self.model_character = YOLO(self.model_character_path)
        self.model_character_dic = {0: '10t', 1: '5.1t', 2: '5t', 3: '8.1t'}
        #结果展示
        self.show_pic = False

        #结果信息
        self.num_weight=5
        self.num_weight_queue = deque(maxlen=5)
        self.total_mass=10.00
        self.total_mass_L=5.00
        self.total_mass_R=5.00
        self.warming_info="安全"

        #配重块重量评估计算
        self.weight_number_dic = {'left': [], 'right': [], 'left_ave': 0.0, 'right_ave': 0.0}

    def process(self,img):
        self.inference(img)
        self._sample_filter()
        slice_result = self._get_image_slice()
        classify_number, character_pos = self._slice_classify(slice_result)

        #需要输出的rgb图像
        annotated_image = self.result[0].plot(conf=True, line_width=2, font_size=None, font="Arial.ttf", pil=False,
                                              img=None, im_gpu=None, kpt_radius=5,
                                              kpt_line=True, labels=True, boxes=True, masks=False, probs=True,
                                              show=False, save=False, filename=None)
        for box in character_pos:
            cv2.rectangle(annotated_image, (box[0], box[1]), (box[2], box[3]), color=(0, 0, 255), thickness=2)
        # rgb_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
        rgb_image = annotated_image

        # 将检测结果添加到队列中
        self.num_weight_queue.append(len(self.result[0].boxes))
        # 获取队列中元素的统计信息
        counter = Counter(self.num_weight_queue)
        # 获取出现次数最多的元素（众数）
        self.num_weight = counter.most_common(1)[0][0]
        # todo
        # 计算配重块质量，self.total_mass_L,self.total_mass_R,self.total_mass,self.num_weight(左边质量、右边质量、总质量、总块数)
        boxes_number = self.result[0].boxes.cpu().numpy().data
        int_boxes_number = np.floor(boxes_number).astype(int)
        self.weight_left_number, self.weight_right_number = knn_classifier(int_boxes_number)
        self.weight_left_number, self.weight_right_number = self.process_weight_number(self.weight_number_dic,
                                                                                       self.weight_left_number,
                                                                                       self.weight_right_number, )
        self.total_mass_L = self.weight_left_number * float(eval(self.model_character_dic[classify_number][0:-1]))
        self.total_mass_R = self.weight_right_number * float(eval(self.model_character_dic[classify_number][0:-1]))
        # 计算完之后对左右数量置为0，避免带入缓存误差
        # self.weight_left_number, self.weight_right_number = 0, 0

        self.total_mass = self.num_weight * float(eval(self.model_character_dic[classify_number][0:-1]))

        # 显示图像
        if self.show_pic:
            show_image(rgb_image)
        return {"CounterWeightNumber":self.num_weight, "TotalWeight":self.total_mass, "LeftWeight":self.total_mass_L, "RightWeight":self.total_mass_R, "Image":rgb_image}

    def inference(self,img):
        self.result = self.yolo_model(img, imgsz=self.imgsz, conf=self.conf, device=self.device)

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
        return
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

    def _get_image_slice(self):
        # 获取原始图像
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
            img_list.append((img_i, conf_list[i], int_boxes[i]))
        return img_list
    def _slice_classify(self, slice_list):
        dic_target = {0:0,1:0,2:0,3:0}
        character_pos=[]
        for slice_img, conf, int_box in slice_list:
            result = self.model_character.predict(slice_img,imgsz=self.imgsz_2,conf=self.conf_2,device=self.device)
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

    def process_weight_number(self,weight_number_dic, weight_left_number, weight_right_number,weight_flag=False):
        if weight_flag==False:
            return weight_left_number, weight_right_number
        if len(weight_number_dic['left']) > 10:
            weight_number_dic['left'] = weight_number_dic['left'][-10:]
        if len(weight_number_dic['right']) > 10:
            weight_number_dic['right'] = weight_number_dic['right'][-10:]

        if len(weight_number_dic['left']) <= 10 or len(weight_number_dic['right']) <= 10:
            weight_number_dic['left'].append(weight_left_number)
            weight_number_dic['right'].append(weight_right_number)
            weight_number_dic['left_ave'] = np.mean(weight_number_dic['left'])
            weight_number_dic['right_ave'] = np.mean(weight_number_dic['right'])

        if len(weight_number_dic['left']) < 2 or len(weight_number_dic['right']) < 2:
            return weight_left_number, weight_right_number
        else:
            if weight_left_number >= (weight_number_dic['left'][-2] - 2) and weight_left_number <= (
                    weight_number_dic['left'][-2] + 2):
                result_left = weight_left_number
            else:
                result_left = round(weight_number_dic['left_ave'])

            if weight_right_number >= (weight_number_dic['right'][-2] - 2) and weight_right_number <= (
                    weight_number_dic['right'][-2] + 2):
                result_right = weight_right_number
            else:
                result_right = round(weight_number_dic['right_ave'])
        return result_left, result_right



if __name__ == '__main__':
    model = yolo_model()
    for i in range(1):
        print(model.process('2.jpg'))
    print('done')

