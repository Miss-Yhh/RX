from datetime import datetime
import cv2
import numpy as np
import onnxruntime as ort
import time
import cv2
import numpy as np
import rospy
from geometry_msgs.msg import Twist

# YOLO 5
class yolov5():
    """
        构造Yolov5运行类
    """

    def __init__(self, modelpath, classnamepath, confThreshold=0.5, nmsThreshold=0.5, objThreshold=0.5):
        with open(classnamepath, 'rt') as f:
            self.classes = f.read().rstrip('\n').split('\n')  # 类别列表
        self.num_classes = len(self.classes)  # 类别个数
        if modelpath.endswith('6.onnx'):
            self.inpHeight, self.inpWidth = 1280, 1280
            anchors = [[19, 27, 44, 40, 38, 94], [96, 68, 86, 152, 180, 137], [140, 301, 303, 264, 238, 542],
                       [436, 615, 739, 380, 925, 792]]
            self.stride = np.array([8., 16., 32., 64.])
        else:
            self.inpHeight, self.inpWidth = 640, 640
            anchors = [[10, 13, 16, 30, 33, 23], [30, 61, 62, 45, 59, 119], [116, 90, 156, 198, 373, 326]]
            self.stride = np.array([8., 16., 32.])
        self.nl = len(anchors)
        self.na = len(anchors[0]) // 2
        self.grid = [np.zeros(1)] * self.nl
        self.anchor_grid = np.asarray(anchors, dtype=np.float32).reshape(self.nl, -1, 2)
        so = ort.SessionOptions()
        so.log_severity_level = 3
        self.net = ort.InferenceSession(modelpath, so)
        self.confThreshold = confThreshold
        self.nmsThreshold = nmsThreshold
        self.objThreshold = objThreshold
        # self.inpHeight, self.inpWidth = (self.net.get_inputs()[0].shape[2], self.net.get_inputs()[0].shape[3])

    def resize_image(self, srcimg, keep_ratio=True):
        top, left, newh, neww = 0, 0, self.inpWidth, self.inpHeight
        if keep_ratio and srcimg.shape[0] != srcimg.shape[1]:
            hw_scale = srcimg.shape[0] / srcimg.shape[1]
            if hw_scale > 1:
                newh, neww = self.inpHeight, int(self.inpWidth / hw_scale)
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                left = int((self.inpWidth - neww) * 0.5)
                img = cv2.copyMakeBorder(img, 0, 0, left, self.inpWidth - neww - left, cv2.BORDER_CONSTANT,
                                         value=(114, 114, 114))  # add border
            else:
                newh, neww = int(self.inpHeight * hw_scale), self.inpWidth
                img = cv2.resize(srcimg, (neww, newh), interpolation=cv2.INTER_AREA)
                top = int((self.inpHeight - newh) * 0.5)
                img = cv2.copyMakeBorder(img, top, self.inpHeight - newh - top, 0, 0, cv2.BORDER_CONSTANT,
                                         value=(114, 114, 114))
        else:
            img = cv2.resize(srcimg, (self.inpWidth, self.inpHeight), interpolation=cv2.INTER_AREA)
        return img, newh, neww, top, left

    def _make_grid(self, nx=20, ny=20):
        xv, yv = np.meshgrid(np.arange(ny), np.arange(nx))
        return np.stack((xv, yv), 2).reshape((-1, 2)).astype(np.float32)

    def preprocess(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        return img
    def postprocess(self, frame, outs, padsize=None):
        frameHeight = frame.shape[0]
        frameWidth = frame.shape[1]
        newh, neww, padh, padw = padsize
        ratioh, ratiow = frameHeight / newh, frameWidth / neww
        # Scan through all the bounding boxes output from the network and keep only the
        # ones with high confidence scores. Assign the box's class label as the class with the highest score.

        confidences = []
        boxes = []
        classIds = []
        for detection in outs:
            if detection[4] > self.objThreshold:
                scores = detection[5:]
                classId = np.argmax(scores)
                if classId != 0:
                    # 只检测人 class == 0
                    continue
                confidence = scores[classId] * detection[4]
                if confidence > self.confThreshold:
                    center_x = int((detection[0] - padw) * ratiow)
                    center_y = int((detection[1] - padh) * ratioh)
                    width = int(detection[2] * ratiow)
                    height = int(detection[3] * ratioh)
                    left = int(center_x - width * 0.5)
                    top = int(center_y - height * 0.5)

                    confidences.append(float(confidence))
                    boxes.append([left, top, width, height])
                    classIds.append(classId)
        # Perform non maximum suppression to eliminate redundant overlapping boxes with
        # lower confidences.
        # indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confThreshold, self.nmsThreshold).flatten()
        # indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confThreshold, self.nmsThreshold)
        indices = np.array(cv2.dnn.NMSBoxes(boxes, confidences, self.confThreshold, self.nmsThreshold)).flatten()
        
        # 找到最大的box
        biggest_confidences = 0
        biggest_classId = 0
        biggest_left = 0
        biggest_top = 0
        biggest_width = 0
        biggest_height = 0
        for i in indices:
            box = boxes[i]
            width = box[2]
            if width > biggest_width:
              biggest_classId = classIds[i]
              biggest_confidences = confidences[i]
              biggest_width = width
              biggest_left = box[0]
              biggest_top = box[1]
              biggest_height = box[3]
        frame = self.drawPred(frame, biggest_classId, biggest_confidences, biggest_left, biggest_top, biggest_left + biggest_width, biggest_top + biggest_height)
        center = int(biggest_left + biggest_width // 2)
        return frame, center, biggest_width

    def drawPred(self, frame, classId, conf, left, top, right, bottom):
        # Draw a bounding box.
        # if classId == 0:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), thickness=2)

        label = '%.2f' % conf
        label = '%s:%s' % (self.classes[classId], label)

        # Display the label at the top of the bounding box
        labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        top = max(top, labelSize[1])
        # cv.rectangle(frame, (left, top - round(1.5 * labelSize[1])), (left + round(1.5 * labelSize[0]), top + baseLine), (255,255,255), cv.FILLED)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), thickness=2)
        return frame

    def detect(self, srcimg):
        img, newh, neww, padh, padw = self.resize_image(srcimg)
        img = self.preprocess(img)
        # Sets the input to the network
        blob = np.expand_dims(np.transpose(img, (2, 0, 1)), axis=0)

        outs = self.net.run(None, {self.net.get_inputs()[0].name: blob})[0].squeeze(axis=0)

        # inference output
        row_ind = 0
        for i in range(self.nl):
            h, w = int(img.shape[0] / self.stride[i]), int(img.shape[1] / self.stride[i])
            length = int(self.na * h * w)
            if self.grid[i].shape[2:4] != (h, w):
                self.grid[i] = self._make_grid(w, h)

            outs[row_ind:row_ind + length, 0:2] = (outs[row_ind:row_ind + length, 0:2] * 2. - 0.5 + np.tile(
                self.grid[i], (self.na, 1))) * int(self.stride[i])
            outs[row_ind:row_ind + length, 2:4] = (outs[row_ind:row_ind + length, 2:4] * 2) ** 2 * np.repeat(
                self.anchor_grid[i], h * w, axis=0)
            row_ind += length
        srcimg, center_x, width = self.postprocess(srcimg, outs, padsize=(newh, neww, padh, padw))
        return srcimg, center_x, width
ctrl_flag = False
import signal

def signal_handler(sig, frame):
    global ctrl_flag
    print('get get ')
    ctrl_flag = True

  
class YoloPub():
    def __init__(self) -> None:
        # 设置 yolov5 网络
        modelpath = '/home/kuavo/catkin_dt/src/checkpoints/yolov5weight/yolov5s.onnx'
        classnamepath = '/home/kuavo/catkin_dt/src/checkpoints/yolov5weight/class.names'
        # self.save_raw_frame = '/Users/winstonwei/Documents/wmj_workspace/xiaohong/ZhanTing/visual_pkg/data_imgs/temp.jpg'
        confThreshold = 0.8
        nmsThreshold = 0.5
        objThreshold = 0.8
        
        self.width = None
        self.encoder = 'vits'
        self.cameraid = 6
        self.raw_video = cv2.VideoCapture(self.cameraid)
        self.yolonet = yolov5(modelpath, classnamepath, confThreshold=confThreshold, nmsThreshold=nmsThreshold, objThreshold=objThreshold)
        
        # 运行网络
        self.yolo_detect()

    def yolo_detect(self):
        signal.signal(signal.SIGINT, signal_handler)
        # 初始化ROS节点
        rospy.init_node('robot_mover', anonymous=True)

        # 创建一个Publisher，发布到/cmd_vel主题，消息类型为Twist
        pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)

        # 创建Twist消息实例
        move_cmd = Twist()

        # 发布消息
        move_cmd.linear.x = 0.0
        pub.publish(move_cmd)
        
        cv2.namedWindow('yolo_depth_bshm', cv2.WINDOW_AUTOSIZE)
        while True and not ctrl_flag:
            ret, frame = self.raw_video.read(0)
            if not ret:
              print('not pic')
              continue
            time1 = datetime.now()
            detect_image, center_x, width = self.yolonet.detect(frame)
            print(width)
            if width < 280:  # 持续发送命令
              # 发布消息
              move_cmd.linear.x = 0.5
              pub.publish(move_cmd)
            else:
              move_cmd.linear.x = 0.0
              pub.publish(move_cmd)
            # cv2.imwrite('/Users/winstonwei/Documents/wmj_workspace/xiaohong/ZhanTing/visual_pkg/data_imgs/temp_alpha_depth_bgr_yolov5.png', detect_image)
            cv2.imshow("yolov5 detect img", detect_image)
            
            key = cv2.waitKey(1)
            if key == 27:
              break

            time.sleep(0.1)
        
        # 停止
        move_cmd.linear.x = 0.0
        pub.publish(move_cmd)
            
def publisher_node():
    # rospy.init_node('I', anonymous=True)
    handler = YoloPub()
    # while (not rospy.is_shutdown()):
    #     pass
    # # spin() simply keeps python from exiting until this node is stopped
    # rospy.spin()

if __name__ == '__main__':
    publisher_node()