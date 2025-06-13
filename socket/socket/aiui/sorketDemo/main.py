"""
一个基于TCP SOCKET 的客户端，用于与指定服务器进行通信，处理不同类型的消息
"""

import struct
import logging
import time
import json
from socket import *
import signal
from processStrategy import *
from threading import Thread, Event
import subprocess


def stop_handle(sig, frame):
    global run
    run = False


signal.signal(signal.SIGINT, stop_handle)
run = True

# 配置日志记录
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 文件日志处理器
file_handler = logging.FileHandler('socket_demo.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

# 终端日志处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)

# 添加处理器到记录器
# logger.addHandler(file_handler)
logger.addHandler(console_handler)


class SocketDemo:
    def __init__(self):
        self.client_socket = None
        self.server_ip_port = ('192.168.21.246', 19199)
        self.server_ip = self.server_ip_port[0]
        self.connected_event = Event()
        self.stop_event = Event()
        self.connect()
        self.start_ping_check()

    def connect(self):
        while not self.stop_event.is_set():
            try:
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = socket(AF_INET, SOCK_STREAM)
                self.client_socket.settimeout(5)  # 设置连接超时
                self.client_socket.connect(self.server_ip_port)
                logging.info(f"Connected to {self.server_ip_port}")
                self.client_socket.settimeout(None)  # 连接成功后取消超时
                self.connected_event.set()
                break
            except (ConnectionError, OSError, timeout) as e:
                logging.error(
                    f"Connection error: {e}. Retrying in 5 seconds...")
                self.connected_event.clear()
                time.sleep(5)

    def receive_full_data(self, expected_length):
        received_data = bytearray()
        while len(received_data) < expected_length:
            try:
                chunk = self.client_socket.recv(
                    expected_length - len(received_data))
                if not chunk:
                    # logging.error("Connection closed by the server.")
                    return None
                received_data.extend(chunk)
            except timeout:
                # logging.error(f"Socket timeout")
                return None
        return bytes(received_data)

    def start_ping_check(self):
        Thread(target=self.ping_check, daemon=True).start()

    def ping_check(self):
        while not self.stop_event.is_set():
            try:
                response = subprocess.run(
                    ["ping", "-c", "1", self.server_ip],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if response.returncode != 0:
                    logging.error(
                        f"Ping to {self.server_ip} failed. Reconnecting...")
                    self.connected_event.clear()
                    self.connect()
            except Exception as e:
                logging.error(f"Error during ping: {e}")
            time.sleep(10)

    def close(self):
        self.stop_event.set()
        if self.client_socket:
            self.client_socket.close()
        logging.info("Socket closed")

    def get_aiui_type(self, data):
        if 'content' in data:
            content = data['content']
            if 'info' in content:
                info = content['info']
                if 'data' in info and isinstance(info['data'], list) and len(info['data']) > 0:
                    data_item = info['data'][0]
                    if 'params' in data_item:
                        params = data_item['params']
                        sub_value = params.get('sub')
                        if sub_value is not None:
                            self.aiui_type = sub_value

    def get_iat_result(self, data):
        # 提取并拼接 w 字段
        words = []
        ws_list = data.get('content', {}).get(
            'result', {}).get('text', {}).get('ws', [])
        for item in ws_list:
            cw_list = item.get('cw', [])
            for cw in cw_list:
                words.append(cw.get('w', ''))
        # 拼接成字符串
        sn_value = data.get('content', {}).get(
            'result', {}).get('text', {}).get('sn')
        ls_value = data.get('content', {}).get(
            'result', {}).get('text', {}).get('ls')
        status_value = -1
        if (sn_value == 1):
            status_value = 0
        elif (ls_value == True):
            status_value = 2
        else:
            status_value = 1
        result_string = ''.join(words)
        if (result_string != "" or status_value == 2):
            logging.info(f"识别结果是: {result_string} {status_value}")

    def get_nlp_result(self, data):
        # 提取 text 字段
        text_value = data.get('content', {}).get(
            'result', {}).get('nlp', {}).get('text')

        status_value = data.get('content', {}).get(
            'result', {}).get('nlp', {}).get('status')

        if text_value is not None and status_value is not None:
            logging.info(f"大模型回答结果是: {text_value}  {status_value}")

    def get_intent_result(self, data):
        text_value = data.get('content', {}).get(
            'result', {}).get('cbm_semantic', {}).get('text')
        intent = json.loads(text_value)
        rc = intent['rc']
        if (rc == 0):
            category = intent.get('category', "")
            logging.info(f"技能结果: {category} ")


    def process(self):
        try:
            self.client_socket.settimeout(3)  # 设置接收超时
            recv_data = self.receive_full_data(7)
            if not recv_data:
                logging.error("No data received. Reconnecting...")
                self.connected_event.clear()
                self.connect()
                return

            if len(recv_data) < 7:
                logging.error(f"Incomplete data received: {recv_data}")
                return

            sync_head, user_id, msg_type, msg_length, msg_id = struct.unpack(
                '<BBBHH', recv_data)

            # 校验接收的数据长度
            msg_data = self.receive_full_data(msg_length + 1)

            if len(msg_data) < msg_length + 1:
                logging.error(f"Incomplete data received: {msg_data}")
                return

            # 解析消息数据
            msg = msg_data[: msg_length]
            # 校检码（最后一个字节）
            check_code = msg_data[-1]

            if sync_head == 0xa5 and user_id == 0x01:
                if msg_type == 0x01:
                    ConfirmProcess().process(self.client_socket, msg_id)
                elif msg_type == 0x04:
                    ConfirmProcess().process(self.client_socket, msg_id)
                    success, result = AiuiMessageProcess().process(self.client_socket, msg)
                    if success:
                        self.aiui_type = ""
                        data = json.loads(result)
                        self.get_aiui_type(data)
                        # logging.info(f"AIUI message processed successfully: {result.decode('utf-8')}")
                        if (self.aiui_type == "iat"):
                            self.get_iat_result(data)

                        elif (self.aiui_type == "nlp"):
                            self.get_nlp_result(data)

                        elif (self.aiui_type == "cbm_semantic"):
                            # pass
                            self.get_intent_result(data)

                        # logging.info(f"AIUI message processed successfully: {result.decode('utf-8')}")
                    else:
                        logging.warning("AIUI message processing failed")
            else:
                return
        except timeout:
            return
        except (ConnectionError, OSError) as e:
            logging.error(
                f"Connection error during process: {e}. Reconnecting...")
            self.connected_event.clear()
            self.connect()


if __name__ == '__main__':
    demo = SocketDemo()
    try:
        while run:
            demo.process()
    finally:
        demo.close()
        logging.info("Program terminated")
