
import json
import os
import wave
import pyaudio
import numpy as np
import subprocess
DURATION = 4
def get_mic_from_head(savepath, timestamp):
    global DURATION
 
    # 定义音频录制的参数
    FORMAT = pyaudio.paInt16  # 数据格式
    CHANNELS = 1  # 通道数，这里假设你有6个麦克风
    RATE = 16000  # 采样率
    CHUNK = 4000  # 每次读取的数据块大小
    RECORD_SECONDS = DURATION  # 录制时间
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

    print("Recording...")
    frames = []
    # 开始录制
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)
    print(total_frames)
    step = 0
    while step < total_frames:
        step += 1
        data = stream.read(CHUNK)
        frame = np.frombuffer(data, dtype=np.int16)
        frames.append(frame)
        energy = np.linalg.norm(frame) // 10000
        print(energy)

        # 一听到有声音,现在的step就重置为0
        # if flag == False:
            # break
    
    print("录音结束。")

    # 停止和关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save the recorded data as a WAV file
    wf = wave.open(savepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # subprocess.run(['ffmpeg','-i', savepath,'-ac','pan=6c|c0=2*c0|c1=0.1*c1|c2=0.1*c2|c3=0.1*c3|c4=0.1*c4|c5=0.1*c5', '-y', savepath])
    
    # 修改为16k
    # savepath_new = savepath.replace(".wav", "16k.wav")
    # cmd = " ".join(['ffmpeg','-i', savepath,'-ar','16000', '-y', savepath_new])
    # process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # code = process.wait()

    # # 删掉48k
    # os.system(f"rm {savepath}")

    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_iat/audiotext4finetune/textpath.json', 'r+', encoding='utf-8') as fj:
        jsondata = json.load(fj)
        # 最后再将生成好的音频文件保存起来
        jsondata[timestamp] = [savepath]
        fj.seek(0)
        json.dump(jsondata, fj, ensure_ascii=False)

if __name__ == '__main__':
    import sys
    savepath = sys.argv[1]
    timestamp = sys.argv[2]
    get_mic_from_head(savepath, timestamp) 
