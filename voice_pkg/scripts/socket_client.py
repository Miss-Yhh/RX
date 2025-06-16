# socket_client.py
import struct
import logging
import time
import json
from socket import *
import signal
from processStrategy import *
from threading import Thread, Event
import subprocess

# 配置日志记录
logger = logging.getLogger(__name__) # Use __name__ to avoid conflicts
if not logger.handlers: # 防止重复添加handler
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

class SocketDemo:
    def __init__(self, result_queue=None):
        self.client_socket = None
        self.server_ip_port = ('192.168.1.104', 19199)
        self.server_ip = self.server_ip_port[0]
        self.connected_event = Event()
        self.stop_event = Event()
        self.aiui_type = ""
        self.result_queue = result_queue # 用于存放IAT结果的队列
        self.connect()
        self.start_ping_check()

    def connect(self):
        while not self.stop_event.is_set():
            try:
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = socket(AF_INET, SOCK_STREAM)
                self.client_socket.settimeout(5)
                self.client_socket.connect(self.server_ip_port)
                logger.info(f"Socket客户端已连接到 {self.server_ip_port}")
                self.client_socket.settimeout(None)
                self.connected_event.set()
                break
            except (ConnectionError, OSError, timeout) as e:
                logger.error(
                    f"Socket连接错误: {e}. 5秒后重试...")
                self.connected_event.clear()
                time.sleep(5)

    def receive_full_data(self, expected_length):
        received_data = bytearray()
        while len(received_data) < expected_length:
            try:
                chunk = self.client_socket.recv(
                    expected_length - len(received_data))
                if not chunk:
                    return None
                received_data.extend(chunk)
            except timeout:
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
                    logger.error(
                        f"Ping to {self.server_ip} 失败. 正在重连...")
                    self.connected_event.clear()
                    self.connect()
            except Exception as e:
                logger.error(f"Ping时出错: {e}")
            time.sleep(10)

    def close(self):
        self.stop_event.set()
        if self.client_socket:
            self.client_socket.close()
        logger.info("Socket客户端已关闭")

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
        words = []
        ws_list = data.get('content', {}).get(
            'result', {}).get('text', {}).get('ws', [])
        for item in ws_list:
            cw_list = item.get('cw', [])
            for cw in cw_list:
                words.append(cw.get('w', ''))
        
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
        
        # 将结果放入队列
        if (result_string != "" or status_value == 2) and self.result_queue is not None:
            logger.info(f"语音识别结果: '{result_string}' (状态: {status_value}) -> 已放入队列")
            self.result_queue.put((result_string, status_value))


    def get_nlp_result(self, data):
        text_value = data.get('content', {}).get(
            'result', {}).get('nlp', {}).get('text')
        status_value = data.get('content', {}).get(
            'result', {}).get('nlp', {}).get('status')
        if text_value is not None and status_value is not None:
            logger.info(f"大模型回答结果是: {text_value} {status_value}")

    def get_intent_result(self, data):
        text_value = data.get('content', {}).get(
            'result', {}).get('cbm_semantic', {}).get('text')
        intent = json.loads(text_value)
        rc = intent['rc']
        if (rc == 0):
            category = intent.get('category', "")
            logger.info(f"技能结果: {category} ")

    def process(self):
        try:
            self.client_socket.settimeout(3)
            recv_data = self.receive_full_data(7)
            if not recv_data:
                # logger.error("未收到数据，可能正在重连...")
                # 在这种情况下，让主循环继续，等待重连成功
                if not self.connected_event.is_set():
                    self.connect()
                return

            if len(recv_data) < 7:
                logger.error(f"收到不完整的数据头: {recv_data}")
                return

            sync_head, user_id, msg_type, msg_length, msg_id = struct.unpack(
                '<BBBHH', recv_data)

            msg_data = self.receive_full_data(msg_length + 1)

            if msg_data is None or len(msg_data) < msg_length + 1:
                logger.error(f"收到不完整的消息体: {msg_data}")
                return

            msg = msg_data[: msg_length]
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
                        if (self.aiui_type == "iat"):
                            self.get_iat_result(data)
                        elif (self.aiui_type == "nlp"):
                            self.get_nlp_result(data)
                        elif (self.aiui_type == "cbm_semantic"):
                            self.get_intent_result(data)
                    else:
                        logger.warning("AIUI消息处理失败")
            else:
                return
        except timeout:
            return
        except (ConnectionError, OSError) as e:
            logger.error(
                f"处理消息时连接错误: {e}. 正在重连...")
            self.connected_event.clear()
            self.connect()