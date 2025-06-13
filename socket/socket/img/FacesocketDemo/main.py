import struct
from socket import *
import signal
from processStrategy import *
import json
import numpy as np
import cv2


def stop_handle(sig, frame):
    global run
    run = False


signal.signal(signal.SIGINT, stop_handle)
run = True


class SocketDemo:
    def __init__(self):
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.server_ip_port = ('192.168.149.51', 9090)
        self.client_socket.connect(self.server_ip_port)
        self.frame_width = 0
        self.frame_height = 0
        self.format = "jpeg"
        self.hasface = False
        self.faceinfo = None

    def close(self):
        self.client_socket.close()

    def recv_all(self, num_byte):
        data = b''
        while len(data) < num_byte:
            packet = self.client_socket.recv(num_byte - len(data))
            if not packet:
                return None
            data += packet
        return data

    def process(self):
        recv_data = self.recv_all(9)
        sync_head, user_id, msg_type, msg_length, msg_id = struct.unpack('<BBBIH', recv_data)
        # 解析消息数据
        # print(hex(sync_head), hex(user_id))
        if sync_head == 0xa5 and user_id == 0x01:
            recv_data = self.recv_all(msg_length + 1)
            if msg_type == 0x07:
                ConfirmProcess().process(self.client_socket, msg_id)
                res = json.loads(recv_data[:-1])
                self.frame_width = res["width"]
                self.frame_height = res["height"]
                self.format = "jpeg" if res["format"] == 1 else "bgr"
            ConfirmProcess().process(self.client_socket, msg_id)
            if msg_type == 0x08:
                frame = cv2.imdecode(np.frombuffer(recv_data[:-1], dtype=np.uint8), cv2.IMREAD_COLOR)
                frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                if self.hasface:
                    x2 = self.faceinfo['x'] + self.faceinfo['w']
                    y2 = self.faceinfo['y'] + self.faceinfo['h']
                    cv2.rectangle(frame, (self.faceinfo['x'], self.faceinfo['y']), (x2, y2), (0, 255, 0), 3)
                cv2.imshow("test", frame)
                cv2.waitKey(1)

            if msg_type == 0x09:
                res = json.loads(recv_data[:-1])
                if "hasFace" in res and "faceInfo" in res:
                    self.hasface = res["hasFace"]
                    self.faceinfo = res["faceInfo"]
                else:
                    self.hasface = False

if __name__ == '__main__':
    demo = SocketDemo()
    try:
        while run:
            demo.process()
    except Exception as e:
        print("Error: ", e)

    finally:
        demo.close()
        cv2.destroyAllWindows()
