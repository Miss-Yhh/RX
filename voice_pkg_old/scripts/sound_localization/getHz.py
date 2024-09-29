import numpy as np
import pyaudio

import numpy as np
import pyaudio

CHUNK = 3000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    # input_device_index=17
)

from scipy.signal import butter, lfilter
def butter_bandstop_filter(lowcut, highcut, fs, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='bandstop')
    return b, a

def apply_fileter(data, fs):
    lowcut = 1200.0
    highcut = 1400.0
    b, a = butter_bandstop_filter(lowcut, highcut, fs, order=2)
    return lfilter(b, a, data)

while True:
    data = stream.read(CHUNK, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.int16)  # 注意使用正确的数据类型

    # samples = apply_fileter(samples, fs=RATE)

    # 计算FFT并获取绝对值
    fft = np.fft.fft(samples)
    abs_fft = np.abs(fft)
    
    # 只考虑正频率部分
    half_index = len(samples) // 2  # FFT结果的一半，对应于正频率
    abs_fft_half = abs_fft[:half_index]
    
    # 在正频率部分找到最大值的索引
    max_freq_index = np.argmax(abs_fft_half)
    sample_freq = np.fft.fftfreq(len(samples), d=1/RATE)[:half_index]
    max_freq = sample_freq[max_freq_index]
    print(f'音频频率: {max_freq} Hz')



    
        