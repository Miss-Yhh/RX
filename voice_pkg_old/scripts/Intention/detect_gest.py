import os
import cv2
import yaml
import queue
import numpy as np
from time import sleep
from collections import deque

import mediapipe as mp

import rospy
from std_msgs.msg import String
from rs2cap_ros import RealSenseCaptureRos

from visualize import draw_gest_landmarks_on_image
from visualize import visualize_finger_direction

# TODO: 增加检测阈值，以避免误检测
# TODO: 增加缓存窗口，以增强稳定性


class HandGestureDetector:
    def __init__(self, image_visulize=False, finger_direction_visulize=False):
        # rospy.init_node('pose_detector', anonymous=True)
        self.pose_pub = rospy.Publisher('pose_chatter', String, queue_size=1)

        self.image_queue = queue.Queue() # 用于存储图像队列
        self.finger_direction_queue = queue.Queue() # 用于存储手指方向队列
        self.image_visulize = image_visulize # 是否可视化图像
        self.finger_direction_visulize = finger_direction_visulize # 是否可视化手指方向

        self.cache = deque(maxlen=10) # 缓存检测到的向量
        self.last_stable_vector = None # 最新的稳定向量

        self.config = self.read_config_file('/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/position_config.yaml')

        self.initialize_hand_landmarker() # 初始化手势识别器

    def initialize_hand_landmarker(self):
        script_dir = os.path.dirname(os.path.abspath(__file__)) # 获取父目录
        model_path = os.path.join(script_dir, 'asset', 'hand_landmarker.task') # 模型路径

        # 初始化手势识别器选项
        options = mp.tasks.vision.HandLandmarkerOptions(
            num_hands=2,
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.IMAGE)

        # 创建手势识别器
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options) 

        # 摄像头输入源
        self.cap = RealSenseCaptureRos()

    def detect_callback(self, result, output_image):
        """手势识别器的回调函数：打印手部识别结果
        """
        start, vector = self.get_gesture_derection(result.hand_landmarks) # 计算向量
        if vector != None:
            self.cache.append(vector) # 将检测结果添加到缓存
        self.get_stable_detection() # 更新稳定向量

        # 可视化手部关键点
        if self.image_visulize:
            annotated_image = draw_gest_landmarks_on_image(output_image, result)
            self.image_queue.put(cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        # 可视化手指方向
        if self.finger_direction_visulize:
            self.finger_direction_queue.put([start, vector])
        
        # TODO: 获取手部的深度信息
        # depth = self.cap.get_depth_at_point(start)

        # print(f"Depth: {depth}")

    def get_gesture_derection(self, landmark_list):
        """获取手指指向的空间块
        """
        # 判断是否检测到手部
        if landmark_list:
            index_to_landmark_part = {
                0: "WRIST", 
                1: "THUMB_CMC", 2: "THUMB_MCP", 3: "THUMB_IP", 4: "THUMB_TIP",
                5: "INDEX_FINGER_MCP", 6: "INDEX_FINGER_PIP", 7: "INDEX_FINGER_DIP", 8: "INDEX_FINGER_TIP",
                9: "MIDDLE_FINGER_MCP", 10: "MIDDLE_FINGER_PIP", 11: "MIDDLE_FINGER_DIP", 12: "MIDDLE_FINGER_TIP",
                13: "RING_FINGER_MCP", 14: "RING_FINGER_PIP", 15: "RING_FINGER_DIP", 16: "RING_FINGER_TIP",
                17: "PINKY_MCP", 18: "PINKY_PIP", 19: "PINKY_DIP", 20: "PINKY_TIP",
            }

            # 识别更高的手
            if len(landmark_list) > 1:
                hand_index = 0 if landmark_list[0][8].y < landmark_list[1][8].y else 1
            else:
                hand_index = 0

            # 获取手腕和食指指尖关键点
            index_finger_mcp = landmark_list[hand_index][5]
            index_finger_tip = landmark_list[hand_index][8]

            # 计算向量
            vector = {
                'x': index_finger_tip.x - index_finger_mcp.x,
                'y': index_finger_tip.y - index_finger_mcp.y,
                'z': index_finger_tip.z - index_finger_mcp.z
            }

            # 对向量进行归一化
            vector_length = (vector['x']**2 + vector['y']**2 + vector['z']**2)**0.5
            vector['x'] /= vector_length
            vector['y'] /= vector_length
            vector['z'] /= vector_length
            
            # 判断向量指向的空间块
            # 定义阈值
            threshold = 0.33
            # x, y, z的值分别为-1, 0, 1，代表向量在该轴向的方向
            space_block = (
                0 if abs(vector['x']) < threshold else (-1 if vector['x'] < 0 else 1),
                0 if abs(vector['y']) < threshold else (-1 if vector['y'] < 0 else 1),
                0 if abs(vector['z']) < threshold else (-1 if vector['z'] < 0 else 1)
            )

            # x: 左右，y: 下上，z: 后前
            return index_finger_mcp, vector
        return None, None
    
    def get_stable_detection(self):
        # 检查队列中最新的向量是否为稳定向量。
        if len(self.cache) < 10:
            return False  # 如果队列中的向量少于10个，则不能认为是稳定的

        for i in range(1, 10):
            if self.vector_angle(self.cache[-1], self.cache[-i-1]) > 20: # 阈值以度为单位
                return False
        self.last_stable_vector = self.cache[-1]
        closest_object = self.vector_to_objects() # 获取最近的物体

        # 发布最近的物体
        closest_object_data = String()
        closest_object_data.data = closest_object
        self.pose_pub.publish(closest_object_data)
        return True
    
    @staticmethod
    def vector_angle(v1, v2):
        vector_1 = [v1['x'], v1['y'], v1['z']]
        vector_2 = [v2['x'], v2['y'], v2['z']]
        # 计算两个向量之间的角度差异（以度为单位）
        unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
        unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        angle_rad = np.arccos(np.clip(dot_product, -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        return angle_deg
    
    @staticmethod
    def read_config_file(filepath):
        with open(filepath, 'r') as file:
            config = yaml.safe_load(file)
        return config

    def vector_to_objects(self):
        direction = self.last_stable_vector
        if direction:
            # 调整方向向量以匹配标准坐标轴
            direction = [direction['x'], direction['z'], -direction['y']]
            direction = np.array(direction)

            # 用户手部大致位置: 正对机器人，面前1.5米，高度1米
            start_point = np.array([0, 1.5, 1])

            # 初始化最接近的物体及其角度
            closest_objects = [(None, np.pi), (None, np.pi)]  # 存储两个最小角度及其对应物体

            robot_pos = np.array([self.config['robot_position']['x'], self.config['robot_position']['y'], self.config['robot_position']['z']])  # 机器人位置
            for exhibit in self.config['exhibits']:
                object_pos = np.array([exhibit['position']['x'], exhibit['position']['y'], exhibit['position']['z']])

                relative_object_pos = object_pos - robot_pos

                object_vector = relative_object_pos - start_point
                object_vector_normalized = object_vector / np.linalg.norm(object_vector)

                angle = np.arccos(np.clip(np.dot(direction, object_vector_normalized), -1.0, 1.0))

                if angle < closest_objects[1][1]:  # 如果当前物体的角度小于第二小的角度
                    if angle < closest_objects[0][1]:  # 如果当前物体的角度也小于最小的角度
                        closest_objects[1] = closest_objects[0]  # 更新第二小的物体为之前的最小物体
                        closest_objects[0] = (exhibit, angle)  # 更新最小的物体为当前物体
                    else:
                        closest_objects[1] = (exhibit, angle)  # 只更新第二小的物体为当前物体

            # 检查最接近的物体和用户指向之间的夹角是否不超过20度
            angle_threshold = np.radians(20)
            if closest_objects[0][1] < angle_threshold:
                print("\nclosest_object:", closest_objects[0][0]['name'])
                return closest_objects[0][0]  # 只返回最接近的物体
            else:
                # 返回最近的两个物品的名字拼接
                objects_names = " ".join([obj[0]['name'] for obj in closest_objects if obj[0] is not None])
                print("\nclosest_objects:", objects_names)
                return objects_names
        else:
            return None

    def run(self):
        # 运行手势识别器
        with self.landmarker as landmarker:
            # 读取视频流
            while True:
                if not self.cap.depth.any() or not self.cap.color.any():
                    # 如果都是空的，也就是一张图片都还没来，就循环等待相机开启
                    print("waiting for camera to open")
                    sleep(1)
                    continue
                depth_image, color_image = self.cap.depth, self.cap.color
                frame = color_image

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # 将摄像头帧从BGR转换为RGB，因为MediaPipe需要RGB格式
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb) # 创建MediaPipe的图像对象

                pose_landmarker_result = landmarker.detect(mp_image) # 手势检测
                self.detect_callback(pose_landmarker_result, output_image=self.cap.color) # 输出结果

                # 可视化标注的图像
                if not self.image_queue.empty():
                    output_image = self.image_queue.get()
                    cv2.imshow("Pose Landmarks", output_image)
                    if cv2.waitKey(5) & 0xFF == 27:
                        break
                
                # 可视化手臂方向
                if not self.finger_direction_queue.empty():
                    elbow, vector = self.finger_direction_queue.get()
                    visualize_finger_direction(elbow, vector)

                sleep(1/10) # 增加显式延迟，避免绘图累计误差

                if rospy.is_shutdown():
                    exit()

if __name__ == "__main__":
    # detector = HandGestureDetector(cap_mode="realsense", image_visulize=True, finger_direction_visulize=True)
    detector = HandGestureDetector(image_visulize=False, finger_direction_visulize=False)
    detector.run()
