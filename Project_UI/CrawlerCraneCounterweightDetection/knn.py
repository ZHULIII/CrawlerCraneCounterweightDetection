"""
author: <Melo>
date: <20240423>
function:<knn classify>
"""
def distance_flag(tmp_point, left_point, right_point):
    distance_left = (left_point[0]-tmp_point[0])**2 + (left_point[1]-tmp_point[1])**2
    distance_right = (right_point[0]-tmp_point[0])**2 + (right_point[1]-tmp_point[1])**2
    if distance_left < distance_right:
        return 0
    return 1

# 使用KNN算法完成对boxes的左右分类
def knn_classifier(int_boxes):
    # 判断int_boxes的初始值
    if int_boxes.shape[0] < 2:
        return int_boxes.shape[0], 0
    # 找到最左，最右的初始值中心点
    left_point, right_point = (float('inf'),float('inf')), (float('-inf'),float('-inf'))
    point_list = []
    for i in range(int_boxes.shape[0]):
        x1, y1, x2, y2 = int_boxes[i][0], int_boxes[i][1], int_boxes[i][2], int_boxes[i][3]
        x,y = (x1 + x2) // 2, (y1 + y2) // 2
        left_point = (y, x) if y < left_point[0] else left_point
        right_point = (y,x) if y > right_point[0] else right_point
        point_list.append((y,x))

    # 迭代更新中心点
    left_count, right_count = 1, 1
    for i in range(len(point_list)):
        tmp_point = point_list[i]
        flag_distance = distance_flag(tmp_point, left_point, right_point)
        if flag_distance == 0:
            tmp_left_point = [(left_point[0]*left_count + tmp_point[0])/(left_count+1), (left_point[1]*left_count + tmp_point[1])/(left_count+1)]
            left_point = (tmp_left_point[0], tmp_left_point[1])
        else:
            tmp_right_point = [(right_point[0] * right_count + tmp_point[0]) / (right_count + 1),
                              (right_point[1] * right_count + tmp_point[1]) / (right_count + 1)]
            right_point = (tmp_right_point[0],tmp_right_point[1])
    total_left = 0
    #对所有点进行距离计算并分类
    for i in range(len(point_list)):
        tmp_point = point_list[i]
        flag_distance = distance_flag(tmp_point, left_point, right_point)
        total_left += (1-flag_distance)
    return total_left, len(point_list)-total_left

# if  __name__ == '__main__':
#     l = [(0, 0,0,0), (5,5,5,6), (10,10,10,10)]
#     import numpy as np
#     l = np.array(l)
#     a, b = knn_classifier(l)
#     print(a,b)
from numba import jit
def write_cache_to_log(log_dir, log_cache):
    try:
        with open(log_dir, 'a') as log_file:
            for log_entry in log_cache:
                log_file.write(log_entry + '\n')
            log_cache = []  # 清空缓存
    except IOError as e:
        print(f"写入日志时发生错误：{e}")

