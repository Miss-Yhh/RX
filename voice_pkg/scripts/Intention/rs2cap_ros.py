# roslaunch realsense2_camera rs_aligned_depth.launch

import pyrealsense2 as rs
import numpy as np
import cv2

import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

class RealSenseCaptureRos:
    def __init__(self):
        rospy.init_node('realsense_capture_ros', anonymous=True)

        self.color_frame_sub = rospy.Subscriber('/camera/color/image_raw', Image, self.color_callback)
        self.depth_frame_sub = rospy.Subscriber('/camera/aligned_depth_to_color/image_raw', Image, self.depth_callback)
        self.color = np.empty([480,640,3], dtype = np.uint8)
        self.depth = np.empty([480,640], dtype = np.float64)

        self.bridge = CvBridge()
    
    def color_callback(self, data):  
        self.color = self.bridge.imgmsg_to_cv2(data, "bgr8")

    def depth_callback(self, data):
        self.depth = self.bridge.imgmsg_to_cv2(data, "16UC1")
    
    def isOpened(self):
        # Check if the camera is opened
        return True
    
    def isOpened(self):
        # Check if the camera is opened
        return True

    def show_images(self, color_image, depth_colormap):  
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', color_image)
        if cv2.waitKey(1) & 0xFF == 27:
            cv2.destroyAllWindows()
            return
