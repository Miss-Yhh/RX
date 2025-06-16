# main_635.py

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
import queue # 新增：导入队列模块

# from test import get_mic_from_audio # 注释掉未使用的导入
import pypinyin
# from mic_ctl import record # 注释掉未使用的导入
from utils import play_sound
# from test_host_3090_iat import kedaxunfei_iat_service # 注释掉未使用的导入
# from test_host_3090_tts import get_tts # 注释掉未使用的导入
# from kedaxunfei_iat.test_webapi_iat_stream import iat_web_api # 注释掉未使用的导入
# from iat import run_iat # 注释掉未使用的导入

from multiprocessing import Process
from tts import get_tts
from XF import XFSerialProtocol, XFJsonProtocol

# 新增：导入我们修改后的Socket客户端
from socket_client import SocketDemo

import rospy
from std_msgs.msg import String, Bool

from GlobalValues import GlobalValuesClass
from qa import intention_detect,stream_qa

# 新增：创建一个全局队列用于线程间通信
IAT_RESULT_QUEUE = queue.Queue()

STATUS = GlobalValuesClass(name="Anythin is OK")
STATUS_DICT = STATUS.get_states_dict()
is_wake = False

record_index=0

def text2speech(text='', index=0, is_beep=False, wavfile=None, ignore_interrupt=False):
    # 此函数保持不变
    if not STATUS.SOUND_OUTPUT_EXIST:
        print(f"喇叭不存在: {text}")
        sleep(1)
        return

    savepath = os.path.join('/home/hit/RX/voice_pkg/temp_record/text2speech/', str(time.time())+'.wav')
    if not wavfile:
        ttsproc = subprocess.Popen(["python3", "/home/hit/RX/voice_pkg/scripts/tts.py", text, savepath])
        while ttsproc.poll() is None:
            if STATUS.is_Interrupted:
                break
    
    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        if STATUS.is_Interrupted:
            STATUS.Last_Play_Processor.kill()
            if not ignore_interrupt:
                return None
            else:
                break
            
    if STATUS.is_Interrupted:
        if not ignore_interrupt:
            return None
        
    if text:
        if is_beep:
            STATUS.set_LAST_BROAD_WORDS(STATUS.LAST_BROAD_WORDS + text)
        else:
            STATUS.set_LAST_BROAD_WORDS(text)
    
    print(f"正在播音...({text})")
    if wavfile:
        savepath = wavfile
    savepath_louder = savepath.replace('.wav', 'louder.wav')
    cmd = f"ffmpeg -loglevel quiet -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -filter:a \"volume={STATUS.SOUND_CHANGE}dB\" -y {savepath_louder}"
    _ = os.system(cmd)
    if STATUS.card_id == -1:
        playproc = subprocess.Popen(["python3", "/home/hit/RX/voice_pkg/scripts/play_sound.py", savepath])
    else:
        playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{savepath_louder}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if index == 1000:
        while playproc.poll() is None:
            if STATUS.is_Interrupted and not ignore_interrupt:
                print('播音被打断')
                playproc.kill()
                return
        STATUS.set_Last_Play_Processor(None)
    else:
        STATUS.set_Last_Play_Processor(playproc)
        time.sleep(0.15)

    return 'tts is over'


# ==============================================================================
# 核心修改部分：替换 listenuser 函数
# ==============================================================================
def listenuser(text='ding', iter=1):
    """
    此函数现在从后台Socket客户端线程获取语音识别结果。
    """
    if STATUS.SOUND_INPUT_EXIST:
        print('------等待用户语音输入 (通过TCP Socket)------')
        # pardon函数处理超时和重试，所以我们可以在这里阻塞。
        # 设置一个超时时间（例如30秒），以防队列长时间没有数据。
        try:
            # 循环从队列中获取，直到获得最终结果（状态码为2）
            while True:
                # 使用超时来防止无限期阻塞
                result_string, status_value = IAT_RESULT_QUEUE.get(timeout=30)
                
                # 状态码 2 代表一句完整的、最终的识别结果
                if status_value == 2:
                    print(f"------收到最终识别结果: '{result_string}'------")
                    # 如果最终结果为空字符串，也视为无效
                    if not result_string:
                        return "####"
                    return result_string
                else:
                    # 状态码 0 或 1 是中间结果，我们忽略它，继续等待最终结果
                    print(f"------收到中间识别结果: '{result_string}' (忽略)------")

        except queue.Empty:
            print("------在指定时间内未收到最终识别结果------")
            # 返回 '####' 以便让 pardon 函数知道需要重试
            return "####"
    else:
        # 保持原来的命令行输入功能作为备用
        userword = input("请输入：")
        return userword
# ==============================================================================

def pardon(pardon_round=1):
    # 此函数保持不变, 它会很好地配合新的 listenuser
    print(f"开始录制用户语音")
    userword = ''
    repeat_count = 0
    while True:
        userword = listenuser('ding', iter=pardon_round)
        if userword and userword != '####':
            print(userword)
            break
        elif userword == '####' or repeat_count < 1:
            text2speech("大家现在可以向我提问", index=1000, is_beep=True)
            repeat_count += 1
        else:
            STATUS.set_is_QAing(False)
            while True:
                if STATUS.is_Interrupted:
                    STATUS.set_is_Interrupted(False)
                    text2speech("大家现在可以向我提问", index=1000, is_beep=True, ignore_interrupt=True)
                    break
            STATUS.set_is_QAing(True)
            STATUS.set_is_Interrupted(False)
    return userword


def record_speech_recognition(recognition_result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/SpeechRecognition.txt', 'a') as f:
        f.write(f"时间：{current_time}\n")
        f.write(f"上一句播音的话：{STATUS.LAST_BROAD_WORDS}\n")
        f.write(f"语音识别结果：{recognition_result}\n\n")

def record_task_classification(user_command, classification_result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/TaskClassification.txt', 'a') as f:
        f.write(f"时间：{current_time}\n")
        f.write(f"用户指令：{user_command}\n")
        f.write(f"分类结果：{classification_result}\n\n")

def record_Youtube(old_question, old_complete_answer, question, answer):
    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/QuestionAnswer.txt', 'a') as f:
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

class InterruptClass:
    def __init__(self, qa_class:object):
        global STATUS
        self.qa_class = qa_class
        self.pre_next_situation = False

    def listen_for_INT(self) -> bool:
        return STATUS.is_Interrupted
    
    def handle_interrupt(self, ):
        name = self.get_self_name() 
        print(f"\n处理 {name} 过程中的打断")
        STATUS.set_is_QAing(True)
        task = '问答意图'
        clear = True 
        while True:
            STATUS.set_is_Interrupted(False)
            self.qa_class.interrupt_stream = True
            print('------task 录制开始时间=', datetime.now())
            question = pardon()
            print('------task 录制结束时间=', datetime.now())
            if '再见' in question or '拜拜' in question:
                play_sound('/home/hit/RX/save_waves/byebye.mp3')
                is_wake=False
                return 0
            elif '系统关机' in question:
                exit(0)
            print('------task 任务判断开始时间=', datetime.now())
            task = intention_detect(question)
            print('------task 任务判断结束时间=', datetime.now())
            if "动作" not in task:
                if clear: 
                    STATUS.set_is_QAing(False) 
                    self.qa_class.answer_question(question)
                    STATUS.set_is_QAing(True)
                else:
                    text2speech('大家还有其他问题吗？', index=1000, is_beep=True)

            if '动作' in task:
                STATUS.set_is_QAing(False)
                cnt = 2
                while cnt>0:
                    print(f"模拟执行动作过程ing......{cnt}")
                    cnt -= 1
                    time.sleep(0.1)
            STATUS.set_is_QAing(False)
    
    def get_self_name(self):
        return self.__class__.__name__

class QAClass():
    def __init__(self):
        self.qaclass_thread = threading.Thread(target=self.QAClassInit,)
        self.qaclass_thread.start()
        self.interrupt_stream = True
        self.task_type_label_list = ['休眠', '继续']
        self.complete_answer = ""
    
    def QAClassInit(self):
        print(1)
    
    def answer_question(self, user_words: str) -> str:
        self.qaclass_thread.join()
        self.interrupt_stream = False
        guodus = ['好', '好的']
        choice = random.randint(0, len(guodus) - 1)
        text = guodus[choice]
        text2speech(text=text, index=0)

        if STATUS.STREAM_RETURN:
            splitters = [',', ';', '.', '!', '?', ':', '，', '。', '！', "'", '；', '？', '：', '/', '\n']
            numbers = [str(c) for c in range(10)]
            buffer = ""
            if_anaphora=False
            
            print(datetime.now())
            for qa_answer in stream_qa(user_words):
                if STATUS.is_Interrupted:
                    print(datetime.now())
                    self.complete_answer = ""
                    self.interrupt_stream = True
                    break
                
                if qa_answer:
                    self.complete_answer += qa_answer
                    buffer += qa_answer
                    if buffer[-1] in splitters:
                        print(datetime.now())
                        text2speech(buffer, index=0)
                        buffer = ""
            if not self.interrupt_stream:
                if buffer:
                    text2speech(buffer, index=1000)
                else:
                    text2speech("？", index=1000)
                self.complete_answer = ""
        else:
            print('非流式返回')
            qa_answer=stream_qa(user_words)
            text2speech(qa_answer, index=1000)
        if self.interrupt_stream:
            sleep(0.05)
            STATUS.set_is_Interrupted(False)
        else:
            pass

class MainClass:
    def __init__(self):
        self.settings() 
        if_card_set_success = self.set_master_index_by_keyword()
        if if_card_set_success:
            STATUS.set_card_id(-1)
        else:
            STATUS.set_card_id(self.get_card_index_by_keyword('ALC'))
        print("\nSTATUS.card_id: ", STATUS.card_id)

        result = self.set_mic_index_by_keyword('alsa_input.usb-iflytek_XFM-DP-V0.0.18_1c00142575854862490-01.mono-fallback')
        if result:
            print('mic set success!')
        else:
            print('mic set error')

        self.qa_class = QAClass()
        self.start = InterruptClass(self.qa_class)
        
        # ==============================================================================
        # 核心修改部分：启动后台Socket客户端线程
        # ==============================================================================
        print("正在初始化并启动后台Socket客户端...")
        # 将全局队列传入客户端实例
        self.socket_demo_client = SocketDemo(IAT_RESULT_QUEUE)
        # 创建并启动守护线程，在后台运行客户端的消息处理循环
        self.socket_thread = threading.Thread(target=self.run_socket_listener, daemon=True)
        self.socket_thread.start()
        # ==============================================================================

        def run_wake_thread():
            # 此处唤醒逻辑保持不变
            global is_wake
            xf = XFSerialProtocol()
            xfj = XFJsonProtocol()
            while True:
                if is_wake:
                    time.sleep(0.1)
                    continue
                msg_id, msg = xf.process()
                print("\033[0;37;44mGet wake up signal.\033[0m")
                is_wake = True
                play_sound('/home/hit/RX/save_waves/please_say.mp3')
                msg_json_str = xfj.processJson(msg)
                wake_info_dict = json.loads(msg_json_str["content"]["info"])["ivw"]

        thread.start_new_thread(run_wake_thread, ())
        print("Initialization finished.")
        
        def run_interrupt_thread():
            # 此处打断逻辑保持不变
            xf = XFSerialProtocol()
            xfj = XFJsonProtocol()
            while True:
                if STATUS.is_Interrupted:
                    time.sleep(0.1)
                    continue
                msg_id, msg = xf.process()
                print("\033[0;37;44mGet wake up signal.\033[0m")
                STATUS.set_is_Interrupted(True)
                play_sound('/home/hit/RX/save_waves/please_say.mp3')
                msg_json_str = xfj.processJson(msg)
                wake_info_dict = json.loads(msg_json_str["content"]["info"])["ivw"]

        while True:
            if not is_wake:
                continue
            
            record_index+=1
            record_start_beep = True
            record_nothing_beep = True
            thread.start_new_thread(run_interrupt_thread, ())

            STATUS.set_is_Interrupted(True)
            self.main()

    # 新增：运行Socket客户端的方法
    def run_socket_listener(self):
        """
        这个方法在后台线程中无限循环，处理来自服务器的所有消息。
        识别结果会自动放入队列中。
        """
        while True:
            # 调用客户端的处理方法，它会处理连接、接收和解析
            self.socket_demo_client.process()
            # 短暂休眠避免CPU占用过高
            time.sleep(0.01)
            
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

    def ivw_callback(self, data):
        if not STATUS.is_QAing:
            print(f"收到打断信号！现在可以打断", datetime.now())
            STATUS.set_is_Interrupted(True)
        else:
            print(f"收到打断信号！现在不可以打断")

    def settings(self):
        STATUS.set_ROBOT_NAME('K')
        STATUS.set_Enable_QA(True)
        STATUS.set_TAKE_ACTION_QA(False)
        STATUS.set_SOUND_INPUT_EXIST(True)
        STATUS.set_SOUND_OUTPUT_EXIST(True)
        STATUS.set_MODEL_TASK_TYPE('qwen1_5')
        STATUS.set_MODEL_LLM_ANSWER('huozi')
        STATUS.set_STREAM_RETURN(True)
        STATUS.set_MODEL_BAN_OPENAI(False)
        STATUS.set_DURATION(15)
        STATUS.set_THRESHOLD_AUDIO(25)
        if STATUS.MODEL_BAN_OPENAI:
            STATUS.set_MODEL_TASK_TYPE('chatglm')
            STATUS.set_MODEL_LLM_ANSWER('chatglm')
    
    def welcome(self):
        while True:
            print("进入welcome阶段")
            sleep(0.05)
            STATUS.set_is_Interrupted(False)
            text2speech("各位游客大家好，我是小红" , index=0)
            STATUS.set_is_QAing(True)
            text2speech("请说 “小红小红” 来唤醒我", index=1000)
            STATUS.set_is_QAing(False)
            print("welcome唤醒提示音结束")
            sound_wake_up_count = 0
            while sound_wake_up_count < 800:
                if STATUS.SOUND_INPUT_EXIST:
                    if STATUS.is_Interrupted:
                        break
                sleep(0.01)
                sound_wake_up_count += 1
            if STATUS.SOUND_INPUT_EXIST:
                if STATUS.is_Interrupted:
                    sleep(0.05)
                    STATUS.set_is_Interrupted(False)
                    break
            
        sleep(0.05)
        STATUS.set_is_Interrupted(False)
        self.main()
  
    def main(self):
        STATUS.set_is_Interrupted(False)
        if_start = self.start.handle_interrupt()

        if if_start == 'start':
            print("开始")

        while True:
            if is_wake:
                if STATUS.Enable_QA :
                    self.start.handle_interrupt()
                    thread.start_new_thread(run_interrupt_thread, ())
            else:
                print('休眠')
                thread.start_new_thread(run_interrupt_thread, ())
        
        text2speech("参观到此结束，欢迎再来哈工大找我玩。", index=1000)
        print("任务结束")
        
if __name__ == "__main__":
    main_class = MainClass()