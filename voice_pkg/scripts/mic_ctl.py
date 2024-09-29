import time
from pydub.playback import play
from pydub import AudioSegment
import pyaudio
import numpy as np
import os
import signal
import sys
from _thread import start_new_thread    
from utils import play_sound    
import queue
import pyaudio
import wave
import numpy as np
import queue
import subprocess
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 4000
DEBUG = False
CLEAN_BUFFER = True

THRESHOLD_AUDIO = 3
WAIT_FOR_START_SECONDS = 3
WAIT_FOR_END_SECONDS = 2
ONE_SECOND_FRAME_NUM = int(RATE / CHUNK)
PRE_USED_SECONDS = 1

p = pyaudio.PyAudio()

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

frames = []  

DURATION=15                  # 无人说话时每轮录音的时间
#THRESHOLD_AUDIO=25 #声音检测的中断阈值

def get_mic_from_audio(record_save_path):    
    # if os.path.exists(record_save_path):
    #     os.remove(record_save_path)
    # time.sleep(0.3)
    
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        # input_device_index=0
    )
    
    print("Begin recording...")
    
    pre_frames = []
    pre_step = 0
    while True:
        pre_step += 1
        data = stream.read(CHUNK, exception_on_overflow=True)
        print("读取的Data size (bytes):", len(data))
        frame = np.frombuffer(data, dtype=np.int16)
        print("frame:",frame)
        energy = np.linalg.norm(frame) // 10000
        
        print(energy)
        
        if energy < THRESHOLD_AUDIO:
            pre_frames.append(frame)
        else:
            pre_frames.append(frame)
            frames = pre_frames[-PRE_USED_SECONDS * ONE_SECOND_FRAME_NUM:]
            pre_frames = []
            break
        
        if pre_step == ONE_SECOND_FRAME_NUM * WAIT_FOR_START_SECONDS:
            stream.stop_stream()
            stream.close()
            p.terminate()
            return False
    
    print("Detect Voice")
    
    step = 0  
    while True:
        step += 1
        data = stream.read(CHUNK, exception_on_overflow=True)
        frame = np.frombuffer(data, dtype=np.int16)
        frames.append(frame)
        
        energy = np.linalg.norm(frame) // 10000

        print(energy)

        if energy > THRESHOLD_AUDIO:
            print("Voice detected. Reset steps to zero.")
            step = 0
        
        if step == ONE_SECOND_FRAME_NUM * WAIT_FOR_END_SECONDS:
            break
    
    print("Recording over.")
 
    audio_data = b''.join(frames)
    audio_segment = AudioSegment(
	    data=audio_data,
	    sample_width=p.get_sample_size(FORMAT),
	    frame_rate=RATE,
	    channels=CHANNELS
	)
   
    frames = []
    
    # if os.path.exists(record_save_path):
    #     os.remove(record_save_path)
    
    audio_segment.export(record_save_path, format="mp3")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    return True
  
from pydub import AudioSegment
import pyaudio
import wave
import numpy as np
import queue

def get_mic_from_audio1(savepath):
    global DURATION
    global THRESHOLD_AUDIO
    global ifinter
    ifinter = False

    # 定义音频录制的参数
    FORMAT = pyaudio.paInt16  # 数据格式
    CHANNELS = 1  # 通道数
    RATE = 16000  # 采样率
    CHUNK = 1000  # 每次读取的数据块大小
    RECORD_SECONDS = DURATION  # 录制时间

    has_sound = False  # 是否有人在说话
    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording:", end='')
    frames = []
    threshold = THRESHOLD_AUDIO  # 音量的能量
    total_valid_frames = 0
    somebodytalking_duration = RATE / CHUNK * 0.2
    stopduration = int(RATE / CHUNK * 0.5)
    bufferlength = int(RATE / CHUNK * 0.5)
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)
    step = 0

    # 准备音频frame的buffer
    audio_q = queue.deque()
    str2terminal = queue.deque()
    for i in range(19):
        str2terminal.append('-')
    
    # 录音循环
    while step < total_frames:
        if ifinter:
            return ''
        step += 1
        data = stream.read(CHUNK, exception_on_overflow=True)
        frame = np.frombuffer(data, dtype=np.int16)
        energy = np.linalg.norm(frame) // 10000
        
        # 如果有声音了，那就加入为frame
        if energy > threshold or len(frames) > 0:
            frames.append(data)  # 直接保存原始数据
        # 不错过前面的frame
        if len(frames) == 0:
            audio_q.append(data)
            if len(audio_q) > bufferlength:
                audio_q.popleft()
            
        # 一听到有声音,现在的step就重置为0，并且静默的时间又回归0.8秒
        if energy > threshold:
            total_valid_frames += 1
            if has_sound == False and total_valid_frames > somebodytalking_duration:
                has_sound = True
            str2terminal.append('+')
            str2terminal.popleft()
            step = 0
            aftersound_frames = stopduration
        else:
            str2terminal.append('-')
            str2terminal.popleft()
        print("\r"+"".join(str2terminal), end='')
        
        # 一旦不再听到声音了，就计算是否到了静默时间
        if energy <= threshold and has_sound == True:
            aftersound_frames -= 1
            if aftersound_frames < 0:
                break
        
    print("录音结束。")

    # 停止和关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()

    if len(frames) == 0:
        return None

    # 将录制的音频保存为 MP3 格式
    audio_data = b''.join(frames)  # 将所有帧拼接在一起
    audio_segment = AudioSegment(
        data=audio_data,
        sample_width=p.get_sample_size(FORMAT),
        frame_rate=RATE,
        channels=CHANNELS
    )

    # 保存为MP3文件
    audio_segment.export(savepath, format="mp3")
    
    print(f"音频已保存到 {savepath}")
    return True





def record(record_start_beep, record_save_path, record_nothing_beep):
    if record_start_beep:
        play_sound('/home/hit/RX/save_waves/please_say.mp3')   # 请说

    
    if CLEAN_BUFFER:
        CHUNK_1 = CHUNK // 4
        # 进行预读取缓存区的清理
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK_1)
        print("Pre-reading to clear buffer...")
        for _ in range(1):  # 进行5次预读取
            print("Pre-reading...[buffer cleaning]")
            data = stream.read(CHUNK_1)
            # 这里可以打印数据或者简单地丢弃它
            # print(np.frombuffer(data, dtype=np.int16))
        print("\033[32mBuffer cleared！ ready to record.\033[0m")
        stream.stop_stream()
        stream.close()
        p.terminate()

    if DEBUG:
        cnt = 10
        while cnt > 0:
            cnt -= 1
            print("等待录音...")
            time.sleep(0.2)
        print('开始录音')
    else:
        time.sleep(0.5)

    if_record_voice = get_mic_from_audio1(record_save_path)  # 录音并保存
    if not DEBUG:
        time.sleep(0.1)
    else:
        print("录音结束...")
        # cnt = 10
        # while cnt > 0:
        #     cnt -= 1
        #     print("录音结束...")
        #     time.sleep(0.2)

    
    if record_nothing_beep and not if_record_voice:
        play_sound('./save_waves/record_nothing_beep.mp3')
        time.sleep(0.5)

    return if_record_voice

if __name__ == "__main__":
    record(record_start_beep=True, record_save_path="mic_record.mp3", record_nothing_beep=True)


    # 爆音可能原因：
    # 1、播音录音软件库不一致
    # 2、缓存区需要清除
