#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import random
from std_msgs.msg import String

from harbin_pkg.srv import doAction # 下位机动作服务

class RobotArmMotionNode(object):
    def __init__(self):
        # 初始化ROS节点
        rospy.init_node('robot_arm_motion_node')

        # 控制循环的标志
        self.should_send_commands = False

        # 创建服务客户端，用于发送指令给机器人硬件
        arm_service = rospy.wait_for_service("/doAction") # 等待与下位机通信的服务变得可用
        self.service_client = rospy.ServiceProxy('/doAction', doAction)

        # 订阅主题
        rospy.Subscriber('arm_chatter', String, self.command_callback)

    def command_callback(self, msg):
        # 当接收到命令时的回调函数
        rospy.loginfo("收到动作指令: %s", msg.data)
        if msg.data == 9000:  # 如果收到的是9000，则开始发送随机数字
            self.should_send_commands = True
            rospy.loginfo("开始发送随机数字给机器人手臂服务")
            self.send_random_numbers()
        elif msg.data == 9001:  # 如果收到的是9001，则停止发送
            self.should_send_commands = False
            rospy.loginfo("停止发送随机数字给机器人手臂服务")
        else:
            rospy.loginfo("发送指定动作: %d", msg.data)
            try:
                # 向服务发送请求，阻塞，直至到达目标点才会返回
                response = self.service_client(action_code=msg.data)
                if response.success:
                    rospy.loginfo("动作执行成功")
                else:
                    rospy.loginfo("动作执行失败")
            except rospy.ServiceException as e:
                rospy.logerr("服务调用失败: %s", e)

    def send_random_numbers(self):
        while self.should_send_commands:
            # 生成随机数字
            random_number = random.randint(1, 10)
            rospy.loginfo("发送随机数字: %d", random_number)
            try:
                # 向服务发送请求，阻塞，直至到达目标点才会返回
                response = self.service_client(action_code=random_number)
                if response.success:
                    rospy.loginfo("动作执行成功")
                else:
                    rospy.loginfo("动作执行失败")
            except rospy.ServiceException as e:
                rospy.logerr("服务调用失败: %s", e)

            rospy.sleep(1)  # 休眠，防止发送过快

    def run(self):
        # 保持节点运行，直到被关闭
        rospy.spin()

if __name__ == '__main__':
    node = RobotArmMotionNode()
    node.run()
