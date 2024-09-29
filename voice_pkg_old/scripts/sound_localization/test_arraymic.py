import wave
import pyaudio
import numpy as np
# import h5py

# 定义音频录制的参数
FORMAT = pyaudio.paInt16  # 数据格式
CHANNELS = 2  # 通道数，这里假设你有6个麦克风
RATE = 16000  # 采样率
CHUNK = 3000  # 每次读取的数据块大小
RECORD_SECONDS = 2  # 录制时间
filename = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/sound_localization/manvoice.wav'
# 初始化PyAudio
p = pyaudio.PyAudio()

# 打开音频流
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                # input_device_index=5
                )

print("Recording...")

frames6 = []
frames61 = []
frames62 = []

# 开始录制
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    frame = np.frombuffer(data, dtype=np.int16)
    frame0 = frame[0::CHANNELS]
    frame1 = frame[1::CHANNELS]
    # frame2 = frame[2::CHANNELS]
    # frame3 = frame[3::CHANNELS]
    # frame4 = frame[4::CHANNELS]
    # frame5 = frame[5::CHANNELS]
    frames6.append(frame)
    frameall1 = frame0
    frameall2 = frame1
    frames61.append(frameall1.tostring())
    frames62.append(frameall2.tostring())

print("Finished recording.")

# Save the recorded data as a WAV file
wf = wave.open(filename.replace('.wav', '6.wav'), 'wb')
wf.setnchannels(2)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames6))
wf.close()

# Save the recorded data as a WAV file
wf = wave.open(filename.replace('.wav', '61.wav'), 'wb')
wf.setnchannels(1)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames61))
wf.close()

# Save the recorded data as a WAV file
wf = wave.open(filename.replace('.wav', '62.wav'), 'wb')
wf.setnchannels(1)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames62))
wf.close()

import subprocess
# subprocess.run(['ffmpeg','-i',filename.replace('.wav', '6.wav'),'-af','pan=6c|c0=0*c0|c1=0*c1|c2=0*c2|c3=0*c3|c4=0*c4|c5=1*c5', '-y', filename.replace('.wav', '6111.wav')])
# '''ffmpeg -i input.wav -af "pan=8c|c0=c0|c1=c1|c2=c2|c3=1.5*c3|c4=c4|c5=c5|c6=c6|c7=c7"'''

subprocess.run(['ffmpeg','-i',filename.replace('.wav', '6.wav'),'-ac','1', '-y', filename.replace('.wav', '6111.wav')])
# subprocess.run(['ffmpeg','-i',filename.replace('.wav', '6.wav'),'-ac','5', '-y', filename.replace('.wav', '6113.wav')])


# 停止和关闭流
stream.stop_stream()
stream.close()
p.terminate()
