import os
import cv2
import queue
import numpy as np
from time import sleep
from collections import deque

import mediapipe as mp

import rospy
from geometry_msgs.msg import Vector3
from rs2cap_ros import RealSenseCaptureRos

from visualize import draw_pose_landmarks_on_image
from visualize import visualize_finger_direction

# TODO: 增加检测阈值，以避免误检测
# TODO: 增加缓存窗口，以增强稳定性


class PoseDetector:
    def __init__(self, image_visulize=False, finger_direction_visulize=False):
        # rospy.init_node('pose_detector', anonymous=True)
        self.pose_pub = rospy.Publisher('pose_chatter', Vector3, queue_size=1)

        self.image_queue = queue.Queue() # 用于存储图像队列
        self.finger_direction_queue = queue.Queue() # 用于存储手臂方向队列
        self.image_visulize = image_visulize # 是否可视化图像
        self.finger_direction_visulize = finger_direction_visulize # 是否可视化手臂方向

        self.cache = deque(maxlen=10) # 缓存检测到的向量
        self.last_stable_vector = None # 最新的稳定向量

        self.initialize_pose_landmarker() # 初始化姿势识别器

    def initialize_pose_landmarker(self):
        script_dir = os.path.dirname(os.path.abspath(__file__)) # 获取父目录
        model_path = os.path.join(script_dir, 'asset', 'pose_landmarker_lite.task') # 模型路径

        # 初始化姿势识别器选项
        options = mp.tasks.vision.PoseLandmarkerOptions(
            num_poses=1,
            min_pose_detection_confidence=0.7,
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.IMAGE)

        # 创建姿势识别器
        self.landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)

        # 摄像头输入源
        self.cap = RealSenseCaptureRos()

    def detect_callback(self, result, output_image):
        """识别器的回调函数：打印姿势识别结果
        """
        start, vector = self.get_pose_direction(result.pose_landmarks) # 计算向量
        if vector != None:
            self.cache.append(vector) # 将检测结果添加到缓存
        self.get_stable_detection() # 检测是否为稳定向量

        # 可视化手臂关键点
        if self.image_visulize:
            annotated_image = draw_pose_landmarks_on_image(output_image, result)
            self.image_queue.put(cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        # 可视化手臂指向方向
        if self.finger_direction_visulize:
            self.finger_direction_queue.put([start, vector])
        
        # TODO: 获取手臂的深度信息
        # depth = self.cap.get_depth_at_point(start)

        # print(f"Depth: {depth}")

    def get_pose_direction(self, landmark_list):
        """获取手臂指向的空间块
        """
        # 判断是否检测到手臂
        if landmark_list != []:
            # 获取肩膀关键点
            left_shoulder = landmark_list[0][11]
            right_shoulder = landmark_list[0][12]

            # 计算双肩向量
            shoulder_vector = {
                'x': left_shoulder.x - right_shoulder.x,
                'y': left_shoulder.y - right_shoulder.y,
                'z': left_shoulder.z - right_shoulder.z
            }

            # 计算双肩向量长度
            shoulder_vector_length = (shoulder_vector['x']**2 + 
                                      shoulder_vector['y']**2)**0.5
            
            # 判断人和摄像头的距离
            if shoulder_vector_length > 0.13 and shoulder_vector_length < 0.22:
                # 获取手肘和手腕关键点
                left_elbow = landmark_list[0][13]
                right_elbow = landmark_list[0][14]
                left_wrist = landmark_list[0][15]
                right_wrist = landmark_list[0][16]

                if left_wrist.y < right_wrist.y:
                    wrist = left_wrist
                    elbow = left_elbow
                else:
                    wrist = right_wrist
                    elbow = right_elbow

                # 计算向量
                vector = {
                    'x': wrist.x - elbow.x,
                    'y': wrist.y - elbow.y,
                    'z': wrist.z - elbow.z
                }

                # 对向量进行归一化
                vector_length = (vector['x']**2 + vector['y']**2 + vector['z']**2)**0.5
                vector['x'] /= vector_length
                vector['y'] /= vector_length
                vector['z'] /= vector_length
                
                # 判断人手臂抬起的高度
                if vector['y'] < 0.8 :
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
                    # print(space_block) # 打印手臂指向的区域
                    return elbow, vector
        return None, None
    
    def get_stable_detection(self):
        # 检查队列中最新的向量是否为稳定向量。
        if len(self.cache) < 10:
            return False  # 如果队列中的向量少于10个，则不能认为是稳定的

        for i in range(1, 10):
            if self.vector_angle(self.cache[-1], self.cache[-i-1]) > 20: # 阈值以度为单位
                return False
        self.last_stable_vector = self.cache[-1]
        self.pose_pub.publish(Vector3(self.last_stable_vector['x'], 
                                      self.last_stable_vector['y'], 
                                      self.last_stable_vector['z']))
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

    def run(self):
        # 运行姿势识别器
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

                pose_landmarker_result = landmarker.detect(mp_image) # 姿势检测
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

                sleep(0.1) # 增加显式延迟，避免绘图累计误差

                if rospy.is_shutdown():
                    exit()

if __name__ == "__main__":
    # detector = PoseDetector(cap_mode="realsense", image_visulize=True, finger_direction_visulize=True)
    detector = PoseDetector(image_visulize=True, finger_direction_visulize=True)
    detector.run()
