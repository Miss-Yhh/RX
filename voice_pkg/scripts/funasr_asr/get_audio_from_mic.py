
import os
import queue
import wave
import pyaudio
import numpy as np
import subprocess
import _thread as thread
from funasr import AutoModel
from datetime import datetime

card_ = 0  # 声卡
flagover = False  # 提示音是否已经读完

DURATION = 10 # 每 $DURATION 秒录音一次
THRESHOLD_AUDIO = 3 # 音量的能量超过阈值 $THRESHOLD_AUDIO，说明有人说话，继续录音


def run_prompt_audio(filename):
    global card_
    # play(AudioSegment.from_wav(filename))
    cmd = f"aplay -D plughw:{card_},0 {filename}"
    exit_status = os.system(cmd)
    global flagover
    flagover = True

def get_mic_from_audio(savepath, haode_audio_path):
    global DURATION
    global THRESHOLD_AUDIO
    
    global flagover
    while flagover == False: continue

 
    # 定义音频录制的参数
    FORMAT = pyaudio.paInt16  # 数据格式
    CHANNELS = 1  # 通道数，这里假设你有6个麦克风
    RATE = 48000  # 采样率
    CHUNK = 4000  # 每次读取的数据块大小
    RECORD_SECONDS = DURATION  # 录制时间
    
    has_sound = False  # 是否有人在说话
    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    # input_device_index=6
                    )

    print("Recording...")
    frames = []
    threshold = THRESHOLD_AUDIO  # 音量的能量
    # 开始录制
    total_valid_frames = 0
    somebodytalking_duration = RATE / CHUNK * 0.2
    stopduration = int(RATE / CHUNK * 0.8)
    bufferlength = int(RATE / CHUNK * 0.5)
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)
    print(total_frames)
    step = 0
    
    # 准备音频frame的buffer
    audio_q = queue.deque()
    
    while step < total_frames:
        step += 1
        data = stream.read(CHUNK)
        frame = np.frombuffer(data, dtype=np.int16)
        energy = np.linalg.norm(frame) // 100
        print(energy)
        
        # 如果有声音了，那就加入为frame
        if energy > threshold or len(frames) > 0:
          frames.append(frame)

        # 不错过前面的frame
        if len(frames) == 0:
          audio_q.append(frame)
          if len(audio_q) > bufferlength:
            audio_q.popleft()
        
        # 一听到有声音,现在的step就重置为0，并且静默的时间又回归0.8秒
        if energy > threshold:
            total_valid_frames += 1
            if has_sound == False and total_valid_frames > somebodytalking_duration:
                # 如果超过了一秒都有声音，说明有人说话了
                has_sound = True
            print(f"检测到声音活动继续录")

            # 持续录制，不会停止
            step = 0
            # 防止说话到一半有继续说，此时应当保证静默时间 仍然是从0.8秒开始减
            aftersound_frames = stopduration
        
        # 一旦不再听到声音了，就计算是否到了静默时间
        if energy <= threshold and has_sound == True:
            print(f"检测到声音衰减")
            aftersound_frames -= 1
            if aftersound_frames < 0:
                # 如果说话之后的静默时间超过一秒
                print('break ---')
                thread.start_new_thread(run_prompt_audio, (haode_audio_path,))
                break
    
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
    wf.writeframes(b''.join(list(audio_q) + frames))
    wf.close()

    # subprocess.run(['ffmpeg','-i', savepath,'-ac','pan=6c|c0=2*c0|c1=0.1*c1|c2=0.1*c2|c3=0.1*c3|c4=0.1*c4|c5=0.1*c5', '-y', savepath])
    
    # 修改为16k
    savepath_new = savepath.replace(".wav", "16k.wav")
    cmd = " ".join(['ffmpeg', '-loglevel quiet', '-i', savepath,'-ar','16000', '-y', savepath_new])
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    code = process.wait()
    
    return savepath_new
 
if __name__ == "__main__":
    
#   model = AutoModel(model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch", model_revision="v2.0.4",
#                     vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch", vad_model_revision="v2.0.4",
#                     punc_model="iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch", punc_model_revision="v2.0.4",
#                     # spk_model="cam++", spk_model_revision="v2.0.2",
#                     )
  while 1:
      input('ready?')
      filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/ding_cut.wav'
      thread.start_new_thread(run_prompt_audio, (filename,))
      
      audiopath = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/audio.wav'
      haode_audio_path = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech/hao_de__pcm.wav'
      
      savepath_new = get_mic_from_audio(audiopath, haode_audio_path)

      time1 = datetime.now()
      res = model.generate(input=savepath_new, 
                  batch_size_s=5000, # 1 token = 60 ms
                  hotword='活子 前进 后退 往前走 小红 等一下 微纳及仿生机器人 刘宏 蔡鹤皋')
      time2 = datetime.now()
      if len(res) > 0:
        print(res[0]['text'])
        print(time2-time1)
