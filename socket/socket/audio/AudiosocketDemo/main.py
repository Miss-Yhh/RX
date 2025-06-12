import struct
from socket import *
import signal
from processStrategy import *
import os
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
        self.server_ip_port = ('192.168.149.51', 9080)
        self.client_socket.connect(self.server_ip_port)
        if os.path.exists('./output.pcm'):
            os.remove('./output.pcm')

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
        sync_head, user_id, msg_type, msg_length, msg_id = struct.unpack(
            '<BBBIH', recv_data)

        if sync_head == 0xa5 and user_id == 0x01:
            recv_data = self.recv_all(msg_length + 1)
            print(f"VAD: {recv_data[0]} 通道号: {recv_data[1]}")
            with open('./output.pcm', 'ab') as pcm_file:
                if (recv_data[1] == 0): # 只保存第0路
                    data = recv_data[8:-1]
                    pcm_file.write(data)


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
