import os
import cv2
import numpy as np

import mediapipe as mp
from mediapipe import solutions
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54)  # vibrant green


def draw_gest_landmarks_on_image(rgb_image, detection_result):
    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness
    annotated_image = np.copy(rgb_image)

    # Loop through the detected hands to visualize.
    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx]

        # Draw the hand landmarks.
        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
            annotated_image,
            hand_landmarks_proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style())

        # Get the top left corner of the detected hand's bounding box.
        height, width, _ = annotated_image.shape
        x_coordinates = [landmark.x for landmark in hand_landmarks]
        y_coordinates = [landmark.y for landmark in hand_landmarks]
        text_x = int(min(x_coordinates) * width)
        text_y = int(min(y_coordinates) * height) - MARGIN

        # Draw handedness (left or right hand) on the image.
        cv2.putText(annotated_image, f"{handedness[0].category_name}",
                    (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

    return annotated_image

def draw_pose_landmarks_on_image(rgb_image, detection_result):
  pose_landmarks_list = detection_result.pose_landmarks
  annotated_image = np.copy(rgb_image)

  # Loop through the detected poses to visualize.
  for idx in range(len(pose_landmarks_list)):
    pose_landmarks = pose_landmarks_list[idx]

    # Draw the pose landmarks.
    pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    pose_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
    ])
    solutions.drawing_utils.draw_landmarks(
      annotated_image,
      pose_landmarks_proto,
      solutions.pose.POSE_CONNECTIONS,
      solutions.drawing_styles.get_default_pose_landmarks_style())
  return annotated_image

# 初始化全局变量
fig = None
ax = None
# 用于缓存
last_valid_wrist = None
last_valid_vector = None

def visualize_finger_direction(wrist, vector):
    global fig, ax, last_valid_wrist, last_valid_vector
    
    # 如果figure不存在或者被关闭了，就创建一个新的
    if fig is None or not plt.fignum_exists(fig.number):
        plt.ion()  # 开启交互模式
        fig = plt.figure(num="Finger Direction")
        ax = fig.add_subplot(111, projection='3d')
    else:
        ax.cla()  # 清除当前axes
    
    # 如果wrist不是None，更新最后一次有效的wrist和vector
    if wrist is not None:
        last_valid_wrist = wrist
        last_valid_vector = vector
    # 如果wrist是None，使用最后一次有效的wrist和vector进行绘图
    else:
        if last_valid_wrist is None or last_valid_vector is None:
            return  # 如果没有最后一次有效的值，直接返回不做绘图
        wrist = last_valid_wrist
        vector = last_valid_vector

    # 绘制向量（从手腕指向食指尖）
    ax.quiver(wrist.x, wrist.z, -wrist.y, vector['x'], vector['z'], -vector['y'], color='blue')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # 设置坐标轴范围
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_zlim(-2, 2)

    # 隐藏刻度线和刻度值
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    # 设置视图角度，让y轴正对屏幕
    ax.view_init(elev=0, azim=0)  # 将方位角设置为-90度

    # 调整留白
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    plt.draw()  # 更新绘图而不阻塞
    plt.pause(0.0001)  # 短暂暂停以允许图形更新

# 使用基于图片的手势检测测试可视化方法
if __name__ == '__main__':
    # 获取父目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'asset', 'hand_landmarker.task')

    # 创建一个手势检测器
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options, num_hands=2)
    detector = vision.HandLandmarker.create_from_options(options)

    # 使用OpenCV启动摄像头
    cap = cv2.VideoCapture(0)  # 0通常是默认的摄像头

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            break

        # 将摄像头帧从BGR转换为RGB，因为MediaPipe需要RGB格式
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 创建MediaPipe的图像对象
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # 检测手势
        detection_result = detector.detect(mp_image)

        # 从检测结果中绘制手势
        annotated_image = draw_gest_landmarks_on_image(mp_image.numpy_view(), detection_result)
        cv2.imshow('Hand Landmarks', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        if cv2.waitKey(5) & 0xFF == 27:  # 按下ESC退出
            break

    cap.release()
    cv2.destroyAllWindows()
