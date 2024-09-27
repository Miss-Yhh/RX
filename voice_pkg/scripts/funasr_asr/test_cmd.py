from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

kwsbp_16k_pipline = pipeline(
    task=Tasks.keyword_spotting,
    model='damo/speech_charctc_kws_phone-xiaoyun-commands',
    model_revision='v1.0.0')


import wave
import numpy as np
import pyaudio
from funasr import AutoModel

# global THRESHOLD_AUDIO
 
# 定义音频录制的参数
FORMAT = pyaudio.paFloat32  # 数据格式
CHANNELS = 1  # 通道数，这里假设你有6个麦克风
RATE = 16000  # 采样率
CHUNK = 9600*2*3//5  # 每次读取的数据块大小
RECORD_SECONDS = 2  # 录制时间
# 初始化PyAudio
p = pyaudio.PyAudio()
# model = AutoModel(model="paraformer-zh-streaming", model_revision="v2.0.4")

# 打开音频流
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                # input_device_index=0
                )

print("Recording...")
frames = []
# 开始录制
cache = {}
chunk_size = [0, 6, 3]
while 1:
    data = stream.read(CHUNK)
    speech_chunk = np.frombuffer(data, dtype=np.float64)
    # res = model.generate(input=speech_chunk, cache=cache, is_final=False, chunk_size=chunk_size, encoder_chunk_look_back=4, decoder_chunk_look_back=1)
    kws_result = kwsbp_16k_pipline(audio_in=speech_chunk)
    if len(kws_result) > 0:
      print(kws_result)
# res = kwsbp_16k_pipline(audio_in='/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/audio16k.wav')
# print(res)

    