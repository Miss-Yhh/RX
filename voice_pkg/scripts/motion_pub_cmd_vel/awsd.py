#!/usr/bin/env python
# 引入必要的库
from datetime import datetime
import time
from yolov5_withdirection import YoloPub
import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import String

def rotate_ahalf(pub, rotate='left'):
    # 设置发布频率
    rate = rospy.Rate(30)  # 30hz

    # 创建Twist消息实例
    move_cmd = Twist()
    
    # 预备
    move_cmd.angular.z = 0.0
    pub.publish(move_cmd)
    
    rate.sleep()
    
    speed = 2 if rotate == 'left' else -2
    move_cmd.angular.z = speed
    for _ in range(10):  # 持续发送命令
        # 发布消息
        pub.publish(move_cmd)
        rate.sleep()
    
    # 等待一会儿，进行下一次发布
    rate.sleep()
        
    # 停止
    move_cmd.angular.z = 0.0
    pub.publish(move_cmd)

stop_flag = False
ctrl_flag = False
import signal
import sys

def signal_handler(sig, frame):
    global ctrl_flag
    print('get get ')
    ctrl_flag = True

  
def continue_rotate(pub, rotate='left'):
    signal.signal(signal.SIGINT, signal_handler)
    global ctrl_flag
    global stop_flag
    stop_flag = False
    ctrl_flag = False
    try:
        # 设置发布频率
        rate = rospy.Rate(30)  # 30hz

        # 创建Twist消息实例
        move_cmd = Twist()
        
        # 预备
        move_cmd.angular.z = 0.0
        pub.publish(move_cmd)
        
        rate.sleep()
        
        speed = 0.5 if rotate == 'left' else -0.5
        move_cmd.angular.z = speed
        
        print(ctrl_flag)
        print(stop_flag)
        while not ctrl_flag and not stop_flag:  # 持续发送命令直到收到停止信号
            pub.publish(move_cmd)
            rate.sleep()
            
        print('finally')

    finally:
        # 停止
        move_cmd.angular.z = 0.0
        pub.publish(move_cmd)
  
  
def rotate_fine350ms(pub, rotate='left'):
    # 设置发布频率
    rate = rospy.Rate(50)  # 50hz

    # 创建Twist消息实例
    move_cmd = Twist()
    
    # 预备
    move_cmd.angular.z = 0.0
    pub.publish(move_cmd)
    
    rate.sleep()
    
    speed = 1 if rotate == 'left' else -1
    move_cmd.angular.z = speed
    for _ in range(40):  # 持续发送命令
        # 发布消息
        pub.publish(move_cmd)
        rate.sleep()
    
    # 等待一会儿，进行下一次发布
    rate.sleep()
        
    # 停止
    move_cmd.angular.z = 0.0
    pub.publish(move_cmd)

def move_forward(pub):
    handler = YoloPub()
  
    # 设置发布频率
    rate = rospy.Rate(30)  # 14hz

    # 创建Twist消息实例
    move_cmd = Twist()
    # 发布消息
    move_cmd.linear.x = 0.0
    pub.publish(move_cmd)
    rate.sleep()
        
    while handler.width == None or handler.width < 700:  # 持续发送命令
        # 发布消息
        move_cmd.linear.x = 0.5
        pub.publish(move_cmd)
        rate.sleep()
        print(11111111)
    
    # 停止
    move_cmd.linear.x = 0.0
    pub.publish(move_cmd)
    
    
def move_robot():
    # 初始化ROS节点
    rospy.init_node('robot_mover', anonymous=True)
    
    # 创建一个Publisher，发布到/cmd_vel主题，消息类型为Twist
    face_sub = rospy.Subscriber("face_chatter", String, face_callback)  # 订阅face话题，检测人脸
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    
    # # 移动半个画面
    # rotate_ahalf(pub, rotate='left')
    
    # # 精调
    # rotate_fine350ms(pub, rotate='right')
    continue_rotate(pub, rotate='left')
    
    # 前进
    # move_forward(pub)

def face_callback(data):
    rospy.loginfo(rospy.get_caller_id() + "I heard %s from face", data.data)
    print(f"人脸回调函数接收到人脸信号")
    """
    人脸位置消息格式：一帧一帧发
        [['LEFT','UP'],['CENTER','RIGHT']] # 第一帧，两个人脸
        ['NOBIGFACE'] # 第二帧,无大脸

    人名格式：
    [
        'songhao',
        'wangjizhe',
        'weimingjie',
        .........
    ]  # 这是一帧。
    """
    face_position_of_frame = eval(data.data)

    print(face_position_of_frame)
    if face_position_of_frame == ["NOBIGFACE"]:
        # STATUS.set_Big_Face_Area("NOBIGFACE")
        pass
    # elif face_position_of_frame[0][0] == "LEFT":  # TODO [0][]只检测了第一个人，可能需要改一下 交给你了jz~！
    #     pass
    #     # STATUS.set_Big_Face_Area("LEFT")
    # elif face_position_of_frame[0][0] == "RIGHT":
    #     pass
        # STATUS.set_Big_Face_Area("RIGHT")
    else:
        # STATUS.set_Big_Face_Area("CENTER")
        global stop_flag
        stop_flag = True
        
    # if self.face_detect_flag:
    #     STATUS.set_is_Big_Face_Detected(True) # 检测到(居中)人脸
    # else:
    #     STATUS.set_is_Big_Face_Detected(False) # 没有检测到(居中)人脸，需要转向
            
if __name__ == '__main__':
    try:
      time1 = datetime.now()
      move_robot()
      time2 = datetime.now()
      print(time2-time1)
    except rospy.ROSInterruptException:
      print(111)
