import re
import os
import ast
import json
import time
import yaml
import random
import inspect
import threading
import subprocess
from time import sleep
import _thread as thread
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from test import get_mic_from_audio
import pypinyin
from mic_ctl import record
from utils import play_sound
from test_host_3090_iat import kedaxunfei_iat_service
from test_host_3090_tts import get_tts
from kedaxunfei_iat.test_webapi_iat_stream import iat_web_api
from iat import run_iat

from multiprocessing import Process
from tts import get_tts
from XF import XFSerialProtocol, XFJsonProtocol


import rospy
from std_msgs.msg import String, Bool

from GlobalValues import GlobalValuesClass
#from interrupt.PPL.api1 import get_llm_answer
from qa0621 import intention_detect,stream_qa

########## NEW/MODIFIED SECTION START ##########
# 新增导入，用于Socket通信和线程安全队列
import socket
import struct
import logging
import zlib
import queue
from abc import abstractmethod, ABC
########## NEW/MODIFIED SECTION END ##########

STATUS = GlobalValuesClass(name="Anythin is OK")
STATUS_DICT = STATUS.get_states_dict()
is_wake = False

########## NEW/MODIFIED SECTION START ##########
# 新增: 定义唤醒词/打断词, 并将is_wake标记为弃用
# is_wake = False # DEPRECATED: 唤醒机制已改变，此变量不再需要
########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
# WAKE_WORD_PATTERN = re.compile(r'小博小博') # DEPRECATED: V6版本已废除所有打断逻辑
########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
########## NEW/MODIFIED SECTION END ##########


record_index=0

def text2speech(text='', index=0, is_beep=False, wavfile=None, ignore_interrupt=False):
    # 如果喇叭不存在就直接跳过
    if not STATUS.SOUND_OUTPUT_EXIST:
        print(f"喇叭不存在: {text}")
        sleep(1)
        return

    ########## NEW/MODIFIED SECTION START ##########
    # 在播报开始前设置正在说话的状态，以便进行打断判断
    # 注意：在原始代码中，这个状态是由is_QAing隐式管理的，这里我们明确化
    STATUS.set_is_QAing(True)
    print(f"DEBUG: 设置状态 is_QAing = True，准备播报 '{text}'")
    ########## NEW/MODIFIED SECTION END ##########

    savepath = os.path.join('/home/niic/RX/voice_pkg/temp_record/text2speech/', str(time.time())+'.wav')
    if not wavfile:
        # #print('not wavfile')
        # tts_process = Process(target=get_tts, args=(text, savepath))

        # # 启动新进程
        # tts_process.start()

        # # 等待进程结束（可选）
        # tts_process.join()

        #/home/hit/RX/voice_pkg/scripts/kedaxunfei_tts/tts_for_test.py

        #print("TTS processing complete.")
        #get_tts(/home/hit/RX/tts.py,text, savepath)
        ttsproc = subprocess.Popen(["python3", "/home/niic/RX/voice_pkg/scripts/tts.py", text, savepath])
        #ttsproc = subprocess.Popen(["/home/hit/RX/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
        # ttsproc = subprocess.Popen(["python3", "/home/hit/RX/tts.py", text, savepath])
        # #ttsproc = subprocess.Popen(["python3", "/home/hit/RX/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
        # print(1)
        while ttsproc.poll() is None:
            #print(1)
            ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
            # if STATUS.is_Interrupted: # DEPRECATED: V6版本已废除所有打断逻辑
            #     #print('被打断')
            #     print('DEBUG: TTS合成过程被提前打断')
            #     break
            time.sleep(0.1) # 在V6版本中，这里仅做普通等待
            ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
        # if STATUS.is_Interrupted: # DEPRECATED: V6版本已废除所有打断逻辑
        #     #print('播音被打断')
        #     STATUS.Last_Play_Processor.kill()
        #     if not ignore_interrupt:
        #         pass
        #     else:
        #         break
        time.sleep(0.1) # 在V6版本中，这里仅做普通等待
        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
    ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
    # if STATUS.is_Interrupted: # DEPRECATED: V6版本已废除所有打断逻辑
    #     if not ignore_interrupt:
    #         print("DEBUG: 播报被打断，重置is_Interrupted标志并返回。")
    #         STATUS.set_is_Interrupted(False)
    #         STATUS.set_is_QAing(False)
    #         return None
    ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
    if text:        #print(text)
        if is_beep:
            #print(1)
            STATUS.set_LAST_BROAD_WORDS(STATUS.LAST_BROAD_WORDS + text)
        else:
            #print(2)
            STATUS.set_LAST_BROAD_WORDS(text)
    print(f"正在播音...({text})")
    if wavfile:
      savepath = wavfile
    savepath_louder = savepath.replace('.wav', 'louder.wav')
    cmd = f"ffmpeg -loglevel quiet -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -filter:a \"volume={STATUS.SOUND_CHANGE}dB\" -y {savepath_louder}"
    _ = os.system(cmd)
    if STATUS.card_id == -1:
        print('111')
        #play_sound(savepath)
        #playproc = Process(target=play_sound, args=(savepath))
        playproc = subprocess.Popen(["python3", "/home/niic/RX/voice_pkg/scripts/utils.py", savepath])        # #tts_process = Process(target=get_tts, args=(text, savepath))
        # print(1)
        # playproc = Process(target=play_sound, args=(savepath,))
        # # 启动新进程
        # playproc.start()
        # playproc.join()
        # print(playproc.is_alive())

        # print(1)
        #playproc = subprocess.Popen(["python3", "/home/hit/RX/voice_pkg/scripts/kedaxunfei_tts/play_sound.py", savepath_louder])
    else:
      print('222')
      #playproc = Process(target=play_sound, args=(savepath))
      #playproc = subprocess.Popen(["python3", "/home/hit/RX/voice_pkg/scripts/utils.py", savepath])
      playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{savepath_louder}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   
    # if index == 1000: # 原逻辑修改如下
    #     while playproc.poll() is None:
    #         if STATUS.is_Interrupted and not ignore_interrupt:
    #             print('播音被打断')
    #             #playproc.terminate()  # 强制终止子进程
    #             playproc.kill()
    #             return
    #     STATUS.set_Last_Play_Processor(None)
    # else:
    #     STATUS.set_Last_Play_Processor(playproc)
    #     time.sleep(0.15)
   
    ########## NEW/MODIFIED SECTION START ##########
    # 使用新的、更健壮的循环来管理播放过程，并替换旧逻辑
    STATUS.set_Last_Play_Processor(playproc)
    while playproc.poll() is None:
        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
        # if STATUS.is_Interrupted and not ignore_interrupt: # DEPRECATED: V6版本已废除所有打断逻辑
        #     print('DEBUG: 播音循环检测到打断信号，终止播报。')
        #     playproc.kill()
        #     STATUS.set_is_Interrupted(False)
        #     STATUS.set_is_QAing(False)
        #     return 'interrupted'
        time.sleep(0.05)
        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########

    STATUS.set_Last_Play_Processor(None)

    # 仅在自然播报结束（非打断）且为长句末尾时，才重置QA状态
    if index == 1000 and not STATUS.is_Interrupted:
        print(f"DEBUG: 播报正常结束，重置状态 is_QAing = False")
        STATUS.set_is_QAing(False)
    ########## NEW/MODIFIED SECTION END ##########

    return 'tts is over'

########## NEW/MODIFIED SECTION START ##########
# 将以下两个函数整体注释掉，因为它们的功能被新的Socket监听机制取代
"""
# DEPRECATED: 该函数及其依赖已被新的Socket监听方式取代
def listenuser(text='ding', iter=1):
    if STATUS.SOUND_INPUT_EXIST:
        record_start_beep=True
        record_nothing_beep=True
        record_indes=time.time()
        #get_mic_from_audio(f"/home/hit/RX/temp_record/record_{record_index}.mp3")
        print('------task 录音开始时间=', datetime.now())


        #get_mic_from_audio(f"/home/hit/RX/temp_record/record_{record_index}.mp3")
        print(1)
        userword = iat_web_api('ding', iter=iter, environment_name='DJI_sitting_at_desk', card=STATUS.card_id)
        print(2)
        #record(record_start_beep, f"/home/hit/RX/temp_record/record_{record_index}.mp3", record_nothing_beep)
        #print('------task 录音结束时间=', datetime.now())


        #record(record_start_beep, f"./temp_record/record_{record_index}.mp3", record_nothing_beep)
        #'/home/hit/RX/voice_pkg/temp_record/text2speech', str(time.time())+'.wav'
        #thread.start_new_thread(play_sound, ("./save_waves/record_over.mp3",))
        #time.sleep(0.8)
        #print('------task 识别开始时间=', datetime.now())

        #userword = run_iat(f"/home/hit/RX/temp_record/record_{record_index}.mp3")
        print('------task 识别结束时间=', datetime.now())
        #userword = run_iat(text, iter=iter, environment_name='DJI_sitting_at_desk', card=STATUS.card_id)
    else:
        userword = input("请输入：")
    return userword

# DEPRECATED: pardon函数的功能将由新的listen_from_socket和InterruptClass.handle_interrupt共同完成
def pardon(pardon_round=1):#参数：迭代次数为1
    print(f"开始录制用户语音")
    userword = ''#存储用户的语音输入
    repeat_count = 0  #记录用户提问的次数
    while True:#进入无限循环，直到成功获取用户语音输入或者满足退出条件
        userword = listenuser('ding', iter=pardon_round)
        if userword and userword != '####':#有效输入：退出
            print(userword)
            break
        elif userword == '####' or repeat_count < 1:
        #没能成功识别用户语音，并且系统还没有重复提示过用户
            #print('大家现在可以向我提问', datetime.now())
            text2speech("大家现在可以向我提问", index=1000, is_beep=True)
            repeat_count += 1
        else:#次数上限，并且未能获取有效输入
            STATUS.set_is_QAing(False)#表示不再处于问答状态
            while True:#进入另一个循环，直到检测到打断信号
                if STATUS.is_Interrupted:                   STATUS.set_is_Interrupted(False)
                    text2speech("大家现在可以向我提问", index=1000, is_beep=True, ignore_interrupt=True)
                    break
            STATUS.set_is_QAing(True)#设置问答状态
            STATUS.set_is_Interrupted(False)#重置打断状态
    return userword
"""
########## NEW/MODIFIED SECTION END ##########

#记录语音识别的结果
def record_speech_recognition(recognition_result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('/home/niic/RX/voice_pkg/scripts/log/SpeechRecognition.txt', 'a') as f:
        f.write(f"时间：{current_time}\n")
        f.write(f"上一句播音的话：{STATUS.LAST_BROAD_WORDS}\n")
        f.write(f"语音识别结果：{recognition_result}\n\n")

#记录用户输入的指令及其分类结果
def record_task_classification(user_command, classification_result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('/home/niic/RX/voice_pkg/scripts/log/TaskClassification.txt', 'a') as f:
        f.write(f"时间：{current_time}\n")
        f.write(f"用户指令：{user_command}\n")
        f.write(f"分类结果：{classification_result}\n\n")

#Jilu问答系统的历史问题以及当前问题，回答，以及参考文档
def record_Youtube(old_question, old_complete_answer, question, answer):
    with open('/home/niic/RX/voice_pkg/scripts/log/QuestionAnswer.txt', 'a') as f:
        f.write(f"上一轮问题：{old_question}\n")
        f.write(f"上一轮回答：{old_complete_answer}\n")
        f.write(f"问题：{question}\n")
        f.write(f"回答：{answer}\n")


def task_class_result_replace(result):
    if '问答' in result:
        return 'qa'
    elif '休眠' in result:
        return 'sleep'
    elif '音量变大' in result:
        return 'soundbig'
    elif '音量变小' in result:
        return 'soundsmall'
    elif '继续' in result:
        return 'continue'
    else:
        return 'bad continue'

########## NEW/MODIFIED SECTION START ##########
# ==============================================================================
# 新增: Socket通信协议处理类 (从 processStrategy.py 整合)
# ==============================================================================
class ProcessStrategy(ABC):
    def makepacket(self, sid, type, content):
        size = len(content)
        temp = bytearray()
        temp.append(0xa5)
        temp.append(0x01)
        temp.append(type)
        temp.append(size & 0xff)
        temp.append((size >> 8) & 0xff)
        temp.append(sid & 0xff)
        temp.append((sid >> 8) & 0xff)
        temp.extend(content)
        temp.append(self.checkcode(temp))
        return temp

    def checkcode(self, data):
        total = sum(data)
        checkcode = (~total + 1) & 0xFF
        return checkcode

    @abstractmethod
    def process(self, client_socket, data):
        pass

class ConfirmProcess(ProcessStrategy):
    def process(self, client_socket, msg_id):
        temp = bytearray()
        temp.append(0xa5)
        temp.append(0x00)
        temp.append(0x00)
        temp.append(0x00)
        send_data = self.makepacket(msg_id, 0xff, temp)
        client_socket.send(send_data)

class AiuiMessageProcess(ProcessStrategy):
    def process(self, client_socket, data):
        if not data:
            return False, bytearray()
        try:
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            output = decompressor.decompress(data)
            output += decompressor.flush()
            return True, output
        except zlib.error as e:
            return False, bytearray()

# ==============================================================================
# 新增: Socket客户端类，用于接收语音识别结果
# ==============================================================================
class VoiceSocketClient:
    """
    一个基于TCP SOCKET的客户端，用于与语音识别服务器通信，
    并将接收到的ASR结果放入一个线程安全的队列中。
    """
    def __init__(self, asr_queue: queue.Queue):
        self.client_socket = None
        self.server_ip_port = ('192.168.1.104', 19199)
        self.asr_queue = asr_queue
        self.stop_event = threading.Event()
        ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) START ##########
        # 新增一个事件，用于从外部控制线程的监听/暂停状态
        self.active_listening_event = threading.Event()
        # 默认启动时是不监听的，由主程序调用resume_listening()来激活
        self.active_listening_event.clear() 
        print("DEBUG: VoiceSocketClient初始化，监听事件默认为关闭状态。")
        ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) END ##########

        # 配置日志
        self.logger = logging.getLogger("VoiceSocketClient")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) START ##########
    def pause_listening(self):
        """外部调用：暂停监听并断开连接"""
        if self.active_listening_event.is_set():
            print("DEBUG: 指令：暂停监听 (pause_listening)")
            self.active_listening_event.clear()

    def resume_listening(self):
        """外部调用：恢复监听并准备连接"""
        if not self.active_listening_event.is_set():
            print("DEBUG: 指令：恢复监听 (resume_listening)")
            self.active_listening_event.set()
    ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) END ##########

    def connect(self):
        # 增加一个检查，如果当前是暂停状态，则不进行连接
        if not self.active_listening_event.is_set():
            time.sleep(0.5) # 在暂停状态下短暂休眠，避免空转
            return False

        # 原有的连接循环
        while not self.stop_event.is_set() and self.active_listening_event.is_set():
            try:
                if self.client_socket:
                    self.client_socket.close()
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(5)
                self.logger.info(f"正在尝试连接到语音服务器 {self.server_ip_port}...")
                self.client_socket.connect(self.server_ip_port)
                self.logger.info(f"成功连接到 {self.server_ip_port}")
                self.client_socket.settimeout(None)
                return True
            except (ConnectionError, socket.error, socket.timeout) as e:
                self.logger.error(f"连接错误: {e}. 5秒后重试...")
                time.sleep(5)
        return False

    def receive_full_data(self, expected_length):
        received_data = bytearray()
        while len(received_data) < expected_length:
            try:
                # 增加检查，如果在接收数据时被命令暂停，则立刻退出
                if not self.active_listening_event.is_set():
                    return None
                chunk = self.client_socket.recv(expected_length - len(received_data))
                if not chunk:
                    return None
                received_data.extend(chunk)
            except socket.timeout:
                return None
        return bytes(received_data)

    def get_iat_result(self, data):
        """从AIUI消息中解析出iat（语音听写）结果，并附带状态码。"""
        try:
            text_data = data.get('content', {}).get('result', {}).get('text', {})
            if not text_data:
                return # 如果不是有效的IAT结果包，则直接返回

            words = []
            ws_list = text_data.get('ws', [])
            for item in ws_list:
                cw_list = item.get('cw', [])
                for cw in cw_list:
                    words.append(cw.get('w', ''))
            result_string = ''.join(words)

            # 解析您发现的状态码 'sn' (sentence number) 和 'ls' (last sentence)
            sn_value = text_data.get('sn')
            ls_value = text_data.get('ls', False) # 如果不存在，默认为False

            status_code = 1 # 默认为中间状态
            if sn_value == 1 and not ls_value:
                status_code = 0  # 句子的开始
            elif ls_value:
                status_code = 2  # 句子的结束
            
            ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
            # if status_code == 2: # DEPRECATED: V6版本已废除所有打断逻辑
            #     print("DEBUG: 句子结束 (status_code=2)，触发打断信号！")
            #     STATUS.set_is_Interrupted(True)
            ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########

            # 将(文本, 状态码)的元组放入队列
            self.logger.info(f"ASR队列输入: ('{result_string}', {status_code})")
            self.asr_queue.put((result_string, status_code))

        except Exception as e:
            self.logger.error(f"解析iat结果时出错: {e}, data: {data}")

    def process_message(self):
        """处理单条从服务器接收的消息"""
        try:
            # 增加检查，如果在等待消息时被命令暂停，则立刻返回False以断开连接
            if not self.active_listening_event.is_set():
                return False

            self.client_socket.settimeout(1) # 使用带超时的接收，以便能周期性地检查暂停标志
            header_data = self.receive_full_data(7)
            if not header_data:
                # 如果是超时，是正常情况，返回True继续循环；如果是连接断开，则返回False
                return isinstance(header_data, bytes) 

            sync_head, user_id, msg_type, msg_length, msg_id = struct.unpack('<BBBHH', header_data)

            msg_data_with_check = self.receive_full_data(msg_length + 1)
            if not msg_data_with_check:
                return False

            msg = msg_data_with_check[:msg_length]

            if sync_head == 0xa5 and user_id == 0x01:
                if msg_type == 0x01 or msg_type == 0x04:
                    ConfirmProcess().process(self.client_socket, msg_id)

                if msg_type == 0x04: # AIUI Message
                    success, result = AiuiMessageProcess().process(self.client_socket, msg)
                    if success:
                        try:
                            data = json.loads(result)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to decode JSON: {e}. Raw data: {result}")
                            return True

                        if not isinstance(data, dict):
                            self.logger.info(f"Received payload is not a dictionary, skipping: {data}")
                            return True

                        content = data.get('content')
                        if not isinstance(content, dict):
                            self.logger.warning(f"Payload 'content' is not a dictionary, skipping: {data}")
                            return True

                        if 'result' in content:
                            self.get_iat_result(data)

                        info_obj = content.get('info')
                        if isinstance(info_obj, dict):
                            sub_type = info_obj.get('data', [{}])[0].get('params', {}).get('sub')
                            if sub_type:
                                ########## MODIFICATION to filter NLP logs (V6) START ##########
                                if sub_type != 'nlp':
                                    self.logger.info(f"Received AIUI info with sub_type: {sub_type}")
                                else:
                                    print(f"DEBUG: 收到并已过滤一条NLP日志。")
                                ########## MODIFICATION to filter NLP logs (V6) END ##########
                            else:
                                self.logger.info(f"Received a dictionary in 'info' field, but no 'sub' type found: {info_obj}")
                        elif info_obj is not None:
                            self.logger.info(f"Received 'info' field as a non-dictionary, skipping parse. Content: {info_obj}")
            return True
        except socket.timeout:
            return True # 超时是正常的，可以继续检查active_listening_event状态
        except (ConnectionError, OSError, struct.error, json.JSONDecodeError) as e:
            self.logger.error(f"处理消息时出错: {e}")
            return False

    def run(self):
        """客户端主循环，根据active_listening_event的状态进行连接或休眠"""
        self.logger.info("语音识别Socket客户端线程已启动。")
        while not self.stop_event.is_set():
            # 等待被主线程激活。如果事件未设置，将在此处阻塞。
            self.active_listening_event.wait()
            
            # 如果线程被要求停止，则退出
            if self.stop_event.is_set():
                break

            # 激活后，尝试连接
            if not self.connect():
                # 如果连接失败（例如网络问题或在连接时被暂停），则清除激活标志并重新等待
                self.logger.warning("连接失败，将返回等待状态。")
                self.active_listening_event.clear()
                continue
            
            # 连接成功后，进入消息处理循环
            # 只要处于激活状态且未被要求停止，就持续处理消息
            while self.active_listening_event.is_set() and not self.stop_event.is_set():
                if not self.process_message():
                    self.logger.warning("消息处理失败或连接断开，将跳出处理循环以尝试重连或等待...")
                    break # 跳出内层循环
            
            # 从消息处理循环退出后（因为被暂停或连接错误），断开socket连接
            if self.client_socket:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.client_socket.close()
                self.client_socket = None
                self.logger.info("Socket客户端已按指令断开连接并进入暂停状态。")

    def close(self):
        self.logger.info("正在关闭Socket客户端...")
        self.active_listening_event.set() # 解除wait的阻塞
        self.stop_event.set() # 设置停止标志
        if self.client_socket:
            self.client_socket.close()
        self.logger.info("Socket客户端已关闭。")

########## NEW/MODIFIED SECTION END ##########


class InterruptClass:
    def __init__(self, qa_class: object, asr_queue: queue.Queue, socket_client: VoiceSocketClient):
        global STATUS
        self.qa_class = qa_class 
        self.asr_queue = asr_queue
        ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) START ##########
        # 保存对socket_client的引用，以便控制它
        self.socket_client = socket_client
        ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) END ##########
        self.pre_next_situation = False 
        print("DEBUG: InterruptClass 初始化，使用新的ASR队列。")

    def listen_for_INT(self) -> bool:
        return STATUS.is_Interrupted

    def listen_from_socket(self):
        """
        新的监听函数(V4)，在监听前会先清空队列中的陈旧消息，
        然后根据状态码(status_code)组装成完整句子。
        """
        # --- 在开始监听前，排空队列中可能残留的旧消息 ---
        try:
            while not self.asr_queue.empty():
                self.asr_queue.get_nowait()
            print("DEBUG: 陈旧的ASR队列已清空，准备接收新指令。")
        except queue.Empty:
            pass # 队列本来就是空的，正常情况
        
        print("\nDEBUG: 开始监听并组装完整句子...")
        final_sentence = ""
        while True:
            try:
                # 从队列中获取(文本片段, 状态码)的元组
                # 增加一个超时以防止在没有结束信号时无限阻塞
                recognized_text, status_code = self.asr_queue.get(timeout=15) 
                print(f"DEBUG: 从队列中获取到片段: ('{recognized_text}', {status_code})")

                # 只有在句子中间过程（状态0或1）且文本非空时，我们才更新最终结果。
                if status_code != 2 and recognized_text:
                    final_sentence = recognized_text
                
                # 当收到结束标志时
                if status_code == 2:
                    # 如果到结束时，我们一句话都没存下来（例如用户只说了一个标点），
                    # 那就把这最后的内容当作结果。
                    if not final_sentence:
                        final_sentence = recognized_text
                    print(f"DEBUG: 收到句子结束标志。最终识别结果: '{final_sentence}'")
                    break  # 句子完整，退出循环

            except queue.Empty:
                print("DEBUG: 监听队列超时，可能用户长时间未说话。返回已有内容。")
                break  # 退出以防止无限等待

        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
        # # if STATUS.is_QAing and WAKE_WORD_PATTERN.search(final_sentence): # DEPRECATED: V6版本已废除所有打断逻辑
        # #     print(f"DEBUG: 在完整句子中检测到打断词！设置is_Interrupted标志为True。")
        # #     STATUS.set_is_Interrupted(True)
        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
            
        return final_sentence
    
    """
    # DEPRECATED: V5及以前的handle_interrupt逻辑已被V6版本取代
    def handle_interrupt(self, ):
        # ... (旧的主循环逻辑) ...
    """

    ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) START ##########
    def handle_interrupt(self, ):
        """处理所有情况下用户指令的新版主循环(V6 - 勿扰模式)。"""
        name = self.get_self_name()
        print(f"\n======== 进入主交互循环 (V6 - {name}) ========")

        while True:
            # --- 1. 聆听阶段 ---
            # 确保打断标志为False
            STATUS.set_is_Interrupted(False)
            # 命令socket客户端开始监听
            print("\nDEBUG: [阶段1/2] 进入聆听模式...")
            self.socket_client.resume_listening()

            # 使用监听函数获取一个完整的用户指令
            question = self.listen_from_socket()

            # --- 2. 处理阶段 (进入“勿扰模式”) ---
            print("DEBUG: [阶段2/2] 进入处理模式（勿扰模式已开启）...")
            # 立刻命令socket客户端暂停监听并断开连接
            self.socket_client.pause_listening()

            # 如果识别结果为空或只有空格，则直接跳过，进入下一轮聆听
            if not question or not question.strip():
                print("DEBUG: 识别结果为空，重新进入聆听模式。")
                continue
            
            # 基本指令处理
            if '再见' in question or '拜拜' in question:
                text2speech('再见，期待下次和您交流。', index=1000)
                # 这里可以添加逻辑来停止整个程序或进入休眠
                print("用户说再见，重新进入聆听模式。")
                continue
            elif '系统关机' in question:
                text2speech('好的，系统即将关闭。', index=1000)
                exit(0)

            # 意图识别
            print('------task 任务判断开始时间=', datetime.now())
            task = intention_detect(question)
            record_task_classification(question, task) # 保留原始日志记录
            print(f'------task 任务判断结束时间=', datetime.now(), f'，结果: {task}')

            if "动作" not in task:
                # 触发问答流程
                self.qa_class.answer_question(question)
            else: # 动作任务
                STATUS.set_is_QAing(False) # 确保执行动作时，可以被新的指令打断
                print(f"模拟执行动作: {task}")
                time.sleep(2) # 模拟动作耗时
                text2speech("动作执行完毕。", index=1000)
            
            print("DEBUG: 当前问答/任务处理完毕，将重新进入聆听模式。")
    ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) END ##########

    def get_self_name(self):
        return self.__class__.__name__

class QAClass():
    def __init__(self):
        #初始化问答模型的线程
        self.qaclass_thread = threading.Thread(target=self.QAClassInit,)
        #启动问答模型的初始化
        self.qaclass_thread.start()
        #标志着问答流是否被打断
        self.interrupt_stream = True

        self.task_type_label_list = ['休眠', '继续']  # 定义可能的任务类型
        #用于存储完整的回答
        self.complete_answer = ""
    def QAClassInit(self):#初始化语言模型类实例
        print(1)
    #     LLMClass = get_llm_answer(model=STATUS.MODEL_LLM_ANSWER, stream_bool=STATUS.STREAM_RETURN)
    #     #get_llm_answer加载大模型
    #     self.llmclass = LLMClass
    def answer_question(self, user_words: str) -> str:
        #问答模型初始化
        self.qaclass_thread.join()
        self.interrupt_stream = False

        #随机选择一个过渡词然后播放
        guodus = ['好', '好的']
        choice = random.randint(0, len(guodus) - 1)
        text = guodus[choice]
        #wavfile = f'/home/hit/RX/voice_pkg/scripts/kedaxunfei_tts/{text}.wav'
        #text2speech(text=text, index=0, wavfile=wavfile)
        text2speech(text=text, index=0)

        if STATUS.STREAM_RETURN:#使用流式返回
            #初始化分隔符和缓存
            splitters = [',', ';', '.', '!', '?', ':', '，', '。', '！', "'", '；', '？', '：', '/', '\n']
            numbers = [str(c) for c in range(10)]  # 数字字符列表
            buffer = ""
            if_anaphora=False
            self.complete_answer = "" # 每次回答前清空

            #调用 self.llmclass.process_query() 来处理用户问题 user_words，
            #并获取流式返回的每个 qa_answer 片段。
            # for qa_answer in self.llmclass.process_query(query=user_words, if_anaphora=if_anaphora, exhibition=STATUS.Current_Area, extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""), commentary_speech=STATUS.COMMENTARY_SPEECH):
            print(datetime.now())
            for qa_answer in stream_qa(user_words):
                ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
                # if STATUS.is_Interrupted:#如果系统被打断 # DEPRECATED: V6版本已废除所有打断逻辑
                #     print(datetime.now())
                #     print("DEBUG: QAClass 检测到打断，停止生成答案。")
                #     #记录问题和已经生成的部分回答
                #     # record_Youtube(self.llmclass.old_question, self.llmclass.old_complete_answer, user_words, self.complete_answer)
                #     self.complete_answer = ""
                #     self.interrupt_stream = True
                #     break
                ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
                #累积答案到缓存
                if qa_answer:
                    self.complete_answer += qa_answer
                    buffer += qa_answer

                    #检查最后一个字符是否是分隔符
                    #如果是则通过TTS播放缓存中的内容
                    if buffer and buffer[-1] in splitters:
                        print(datetime.now())
                        text2speech(buffer, index=0)
                        buffer = ""

            if not self.interrupt_stream:#如果没有被打断
                if buffer:#如果循环结束后，缓存里面仍然有内容，播放他
                    text2speech(buffer, index=1000)
                else:#如果没有剩余内容就播放一个？
                    text2speech("？", index=1000)
                #记录完整的问答过程
                #record_Youtube(self.llmclass.old_question, self.llmclass.old_complete_answer, user_words, self.complete_answer)
                self.complete_answer = ""
        else:#非流式返回的处理
            print('非流式返回')
            #直接获取完整的回答
            # qa_answer = self.llmclass.process_query(user_words, if_anaphora=if_anaphora, exhibition=STATUS.Current_Area, extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""), commentary_speech=STATUS.COMMENTARY_SPEECH)
            qa_answer=stream_qa(user_words)
            #record_Youtube(self.llmclass.old_question, self.llmclass.old_complete_answer, user_words, qa_answer)
            #记录下来然后一次性播放
            text2speech(qa_answer, index=1000)

        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) START ##########
        # if self.interrupt_stream:#如果问答被打断就等待50ms # DEPRECATED: V6版本已废除所有打断逻辑
        #     sleep(0.05)
        #     STATUS.set_is_Interrupted(False)
        ########## MODIFICATION FOR NEW INTERRUPTION LOGIC (V6) END ##########
        # else:
        #     pass
            # text2speech('我说完了，大家还有问题吗？', index=1000, is_beep=True)
        # STATUS.set_is_QAing(False)


class MainClass:
    def __init__(self):
        self.settings() #调用setting方法，配置全局设置

        #设置声卡
        if_card_set_success = self.set_master_index_by_keyword()#尝试通过关键词设置主声卡
        if if_card_set_success:
            STATUS.set_card_id(-1)## 如果成功设置声卡，设置全局状态的 card_id 为 -1
        else:
            STATUS.set_card_id(self.get_card_index_by_keyword('ALC'))## 如果设置失败，尝试通过另一个关键词 ALC 来设置声卡。
        print("\nSTATUS.card_id: ", STATUS.card_id)#打印设置的声卡的id

        #这是麦克风
        result = self.set_mic_index_by_keyword('alsa_input.usb-iflytek_XFM-DP-V0.0.18_1c00142575854862490-01.mono-fallback')
        if result:
            print('mic set success!')
        else:
            print('mic set error')
        
        ########## NEW/MODIFIED SECTION START ##########
        # 1. 初始化线程安全的ASR结果队列
        self.asr_queue = queue.Queue()

        # 2. 初始化并启动Socket客户端线程
        print("DEBUG: 初始化 VoiceSocketClient...")
        self.socket_client = VoiceSocketClient(self.asr_queue)
        self.socket_thread = threading.Thread(target=self.socket_client.run, daemon=True)
        self.socket_thread.start()
        print("DEBUG: VoiceSocketClient 线程已启动。")
        
        # 3. 初始化问答和打断处理类，并传入ASR队列
        self.qa_class = QAClass()#实例化问答类
        ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) START ##########
        # 将socket_client实例也传入，以便主循环可以控制它
        self.start = InterruptClass(self.qa_class, self.asr_queue, self.socket_client)
        ########## MODIFICATION FOR NEW DEAF MODE LOGIC (V6) END ##########
        
        """
        # DEPRECATED: 旧的初始化方式
        self.qa_class = QAClass()#实例化问答类
        self.start = InterruptClass(self.qa_class)#实例化打断处理类
        """
        ########## NEW/MODIFIED SECTION END ##########

        # rospy.init_node('interrupt', anonymous=False)
        # # # 初始化 ROS 节点，节点名为 'interrupt'，anonymous=False 表示不使用匿名名称。
        # print(1)

        # if STATUS.SOUND_INPUT_EXIST:#存在录音设备
        #     print(1)
        #     ## 订阅 ivw_chatter 话题，监听唤醒词
        #     # rospy.Subscriber 监听某个话题的消息，当有新消息发布的时候调用指定的回调函数
        #     self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback)
        #     #也就是说，每当有新消息发布时，调用ivw_callback来处理收到的消息
        #     #这里的ivw_chatter可能是一个语音识别节点，监测用户的语音，监测到唤醒词时就发布一个包含唤醒信号的消息。
        record_index=0

        ########## NEW/MODIFIED SECTION START ##########
        """
        # DEPRECATED: 整个唤醒和中断线程逻辑被Socket机制取代
        def run_wake_thread():
            global is_wake
            xf = XFSerialProtocol()
            xfj = XFJsonProtocol()
            while True:
                if is_wake:
                    # 如果是唤醒状态，不需要再次唤醒
                    time.sleep(0.1)
                    continue

                msg_id, msg = xf.process()
                print("\033[0;37;44mGet wake up signal.\033[0m")
                is_wake = True
                play_sound('/home/hit/RX/save_waves/please_say.mp3')


                msg_json_str = xfj.processJson(msg)
                wake_info_dict = json.loads(msg_json_str["content"]["info"])["ivw"]
                # {'start_ms': 1323880, 'end_ms': 1324900, 'beam': 5, 'physical': 5, 'score': 1111.0, 'power': 3273681.5, 'angle': 270.0, 'keyword': 'ni3 hao3 ling2 bo2'}

        thread.start_new_thread(run_wake_thread, ())

        print("Initialization finished.")
        def run_interrupt_thread():

            xf = XFSerialProtocol()
            xfj = XFJsonProtocol()
            while True:
                if STATUS.is_Interrupted:
                    # 如果是唤醒状态，不需要再次唤醒
                    time.sleep(0.1)
                    continue

                msg_id, msg = xf.process()

                print("\033[0;37;44mGet wake up signal.\033[0m")

                STATUS.set_is_Interrupted(True)
                play_sound('/home/hit/RX/save_waves/please_say.mp3')

                msg_json_str = xfj.processJson(msg)
                wake_info_dict = json.loads(msg_json_str["content"]["info"])["ivw"]
                # {'start_ms': 1323880, 'end_ms': 1324900, 'beam': 5, 'physical': 5, 'score': 1111.0, 'power': 3273681.5, 'angle': 270.0, 'keyword': 'ni3 hao3 ling2 bo2'}

        while True:
            if not is_wake:
                continue
            record_index+=1
            record_start_beep = True
            record_nothing_beep = True
            thread.start_new_thread(run_interrupt_thread, ())
        #     if_record_voice = record(record_start_beep, f"/home/hit/RX/temp_record/record_{record_index}.mp3", record_nothing_beep)

        #     while not if_record_voice:
        #         record_start_beep = False
        #         print('录音失败')
        #         #if_record_voice = record(record_start_beep, f"/home/hit/RX/temp_record/record_{record_index}.mp3", record_nothing_beep)


        #     #thread.start_new_thread(play_sound, ("/home/hit/RX/save_waves/record_over.mp3",))
        #     print('好的我听见了')
        #     #time.sleep(0.8)

        #     #get_iat_server(f"/home/hit/RX/temp_record/record_{record_index}.mp3", 3090)
        #     #query = kedaxunfei_iat_service(f"/home/hit/RX/temp_record/record_{record_index}.mp3")
        #     query = run_iat(f"/home/hit/RX/temp_record/record_{record_index}.mp3")
        #     print(f"\033[33m识别结果: {query}\033[0m")


        #     if query.strip() == "":
        #         print('很抱歉我没能理解您的意思')
        #         #play_sound("./save_waves/iat_nothing_beep.mp3")  # 很抱歉，我没有理解您的意思
        #         time.sleep(0.5)
        # # 根据关键词执行特定逻辑
        #     else:
        #         if not STATUS.is_QAing:#如果当前没有进行问答，设置状态为已经打断
        #             print(f"收到打断信号！现在可以打断", datetime.now())
        #             STATUS.set_is_Interrupted(True)
        #             print("\033[33mGlobalValues---INFO---\033[0m")#打印全局信息
        #             #self.welcome()#调用welcome方法，执行迎宾流程
        #             self.main()
        #             break
        #         else:#如果问答，不允许打断
        #             print(f"收到打断信号！现在不可以打断")
        #             break
            STATUS.set_is_Interrupted(True)
            self.main()
        """
        
        print("="*20)
        print("系统初始化完成，进入主交互模式。")
        print("="*20)

        # 程序启动后直接开始主交互流程
        self.welcome()
        ########## NEW/MODIFIED SECTION END ##########


    def get_card_index_by_keyword(self, keyword):
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error executing arecord -l")
            return None
        match = re.search(r'card (\d+):.*' + re.escape(keyword), result.stdout)
        if match:
            return int(match.group(1))
        else:
            return None

    def set_master_index_by_keyword(self, keyword='alsa_output.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.analog-stereo'):
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error executing arecord -l")
            return None
        match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
        if match:
            masterid = int(match.group(1))
        else:
            return False
        result = subprocess.run(['pactl', 'set-default-sink', str(masterid)], capture_output=True, text=True)
        return True

    def set_mic_index_by_keyword(self, keyword):
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error executing arecord -l")
            return None
        match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
        if match:
            micid = int(match.group(1))
        else:
            return False
        result = subprocess.run(['pactl', 'set-default-source', str(micid)], capture_output=True, text=True)
        return True

    # 处理 ivw 话题的回调函数，用于处理唤醒词的回调
    def ivw_callback(self, data):
        if not STATUS.is_QAing:#如果当前没有进行问答，设置状态为已经打断
            print(f"收到打断信号！现在可以打断", datetime.now())
            STATUS.set_is_Interrupted(True)
        else:#如果问答，不允许打断
            print(f"收到打断信号！现在不可以打断")

    def settings(self):
        STATUS.set_ROBOT_NAME('K')#机器人名称

        STATUS.set_Enable_QA(True)#开启问答功能

        STATUS.set_TAKE_ACTION_QA(False)#问答时是否需要机器人做动作

        STATUS.set_SOUND_INPUT_EXIST(True)#是否存在录音设备
        STATUS.set_SOUND_OUTPUT_EXIST(True)#播音设备

        STATUS.set_MODEL_TASK_TYPE('qwen1_5')    # chatglm gpt-4 gpt-3.5-turbo qwen1_5
        #设置大语言模型任务类型

        STATUS.set_MODEL_LLM_ANSWER('huozi')#设置用于回答的任务类型

        STATUS.set_STREAM_RETURN(True)#是否采用流式输出
        STATUS.set_MODEL_BAN_OPENAI(False)#是否禁用openai

        STATUS.set_DURATION(15)#无人讲话时每轮录音持续时间为15
        STATUS.set_THRESHOLD_AUDIO(25)#录音的音量阈值，超过25代表有人讲话

        if STATUS.MODEL_BAN_OPENAI:#如果openai被禁用，备用的模型
            STATUS.set_MODEL_TASK_TYPE('chatglm')
            STATUS.set_MODEL_LLM_ANSWER('chatglm')
        # STATUS.print_all_status()#打印当前所有状态

    #用于迎接用户和唤醒机器ンの阶段
    def welcome(self):
        ########## NEW/MODIFIED SECTION START ##########
        # 新的欢迎流程，不再等待唤醒，直接进入主交互
        print("DEBUG: 进入 welcome 阶段 (新版)")
        text2speech("大家好，我是小博，我已经准备好和大家交流了。", index=1000)
        # 直接进入主交互循环
        self.main()
        """
        # DEPRECATED: 旧的欢迎流程，依赖于硬件中断唤醒
        while True:
            print("进入welcome阶段")

            sleep(0.05)
            STATUS.set_is_Interrupted(False)#打断状态设置为false

            text2speech("各位游客大家好，我是小博" , index=0)
            STATUS.set_is_QAing(True)#设置问答状态为true
            text2speech("请说 “小博小博” 来唤醒我", index=1000)
            STATUS.set_is_QAing(False)

            print("welcome唤醒提示音结束")

            #语音唤醒检测的内循环
            sound_wake_up_count = 0
            while sound_wake_up_count < 800:
                if STATUS.SOUND_INPUT_EXIST:#如果录音设备存在
                    if STATUS.is_Interrupted:#如果监测到打断信号
                        break
                sleep(0.01)
                sound_wake_up_count += 1#增加唤醒计数

            #这里刚刚跳出了800的循环，如果接受到打断信号，并且录音设备存在
            if STATUS.SOUND_INPUT_EXIST:
                if STATUS.is_Interrupted:
                    sleep(0.05)
                    STATUS.set_is_Interrupted(False)
                    break
        sleep(0.05)
        STATUS.set_is_Interrupted(False)
        #重置打断状态，set_is_Interrupted这个是一个函数，作用是设置is_Interrupted的值
        #系统就可以继续处理新的打断
        self.main()
        """
        ########## NEW/MODIFIED SECTION END ##########


    #所以说执行到main（）时，一定已经被唤醒
    def main(self):
        ########## NEW/MODIFIED SECTION START ##########
        # 新的主函数入口，直接启动打断处理循环
        try:
            # handle_interrupt现在是一个无限循环，将处理所有交互
            self.start.handle_interrupt()
        except KeyboardInterrupt:
            print("\n接收到Ctrl+C，正在关闭程序...")
        finally:
            self.socket_client.close()
            print("程序已安全退出。")
        """
        # DEPRECATED: 旧的主函数逻辑，依赖于唤醒
        STATUS.set_is_Interrupted(False)
        if_start = self.start.handle_interrupt()
        #通过 handle_interrupt 函数处理用户打断信号，获取是否开始参观的指令

        #如果用户选择开始参观
        if if_start == 'start':
            print("开始")


        while True:
            if is_wake:
                # 如果开启问答功能，且讲解成功并且没有额外导航点，则进入问答环节
                if STATUS.Enable_QA :
                    #print(f"\n执行问答\n")
                    self.start.handle_interrupt()
                    thread.start_new_thread(run_interrupt_thread, ())

            else:
                print('休眠')
                thread.start_new_thread(run_interrupt_thread, ())
        text2speech("参观到此结束，欢迎再来哈工大找我玩。", index=1000)
        print("任务结束")
        """
        ########## NEW/MODIFIED SECTION END ##########

if __name__ == "__main__":
    # main_class = MainClass() # 原有启动方式
    ########## NEW/MODIFIED SECTION START ##########
    # 使用try-except包裹，以便在初始化失败时也能优雅退出
    try:
        main_class = MainClass()
    except KeyboardInterrupt:
        print("\n程序在初始化过程中被强制退出。")
    except Exception as e:
        print(f"\n程序启动时发生未捕获的异常: {e}")
        logging.exception("程序启动失败") # 记录详细的异常追溯
    ########## NEW/MODIFIED SECTION END ##########