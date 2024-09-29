# import librosa
# import numpy as np
# import time

# import pyaudio

# # PyAudio的信号采集参数
# CHUNK = 1024
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100
# p = pyaudio.PyAudio()
# stream = p.open(
#     format=FORMAT,
#     channels=CHANNELS,
#     rate=RATE,
#     input=True,
#     frames_per_buffer=CHUNK,
#     input_device_index=13
# )

# while True:
#     data = stream.read(CHUNK, exception_on_overflow=False)
#     audio_array = np.frombuffer(data, dtype=np.int16)

# Print out realtime audio volume as ascii bars

import pyaudio
import sounddevice as sd
import numpy as np

def print_sound(indata, outdata, frames, time, status):
    volume_norm = np.linalg.norm(indata)*10
    print ("|" * int(volume_norm))

# with sd.Stream(callback=print_sound):
#     sd.sleep(10000)

def get_audio_from_ad():
    print("Recording...")
    frames = []
    threshold = 100  # 音量的能量
    # 开始录制
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)
    print(total_frames)
    step = 0
    while step < total_frames:
        step += 1
        data = stream.read(CHUNK, exception_on_overflow=False)
        frame = np.frombuffer(data, dtype=np.int16)
        frames.append(frame)
        # energy = sound_energy(frame)
        volume_norm = np.linalg.norm(frame) // 10000
        print ("|" * int(volume_norm), int(volume_norm))
        # print(volume_norm)


# 定义音频录制的参数
FORMAT = pyaudio.paInt16  # 数据格式
CHANNELS = 6  # 通道数，这里假设你有6个麦克风
RATE = 16000  # 采样率
CHUNK = 3000  # 每次读取的数据块大小
RECORD_SECONDS = 100  # 录制时间
# 初始化PyAudio
p = pyaudio.PyAudio()

# 打开音频流
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=5
                )

# get_mic('/home/robot/soundposition/manvoice_sd.wav')
get_audio_from_ad()