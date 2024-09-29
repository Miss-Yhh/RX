#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 接收安卓板发送的导航目标 navigation_request

import grpc
from concurrent import futures

from android_msg_pb2 import server_reply
from android_msg_pb2_grpc import NavsystemServicer, add_NavsystemServicer_to_server

import rospy
from std_msgs.msg import String

class navsysServicer(NavsystemServicer):
    def start_nav_queue(self, request, context):
        navigation_request = request.mode
        
        print("get navigation_request: " + navigation_request)
        Touchpad_pub.publish(navigation_request)
        
        return server_reply(ret_code="ok")

def serve():    
    port = "5678"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_NavsystemServicer_to_server(navsysServicer(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

if __name__ == '__main__':
    rospy.init_node("android_")
    Touchpad_pub = rospy.Publisher("touchpad_navi", String, queue_size=1)
    serve()
