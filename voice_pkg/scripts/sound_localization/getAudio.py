import wave
import pyaudio
import numpy as np
# import h5py



# from scipy.signal import butter, lfilter
# def butter_bandstop_filter(lowcut, highcut, fs, order=2):
#     nyq = 0.5 * fs
#     low = lowcut / nyq
#     high = highcut / nyq
#     b, a = butter(order, [low, high], btype='bandstop')
#     return b, a

# def apply_fileter(data, fs):
#     lowcut = 800.0
#     highcut = 1400.0
#     b, a = butter_bandstop_filter(lowcut, highcut, fs, order=2)
#     return lfilter(b, a, data)



# def remove_noise_freq(data, lower_bound, upper_bound, rate):
#     # FFT
#     fft_data = np.fft.fft(data)
#     freqs = np.fft.fftfreq(len(fft_data), 1/rate)
    
#     # 找到需要去除的频率范围的索引
#     idx_band = np.where((freqs >= lower_bound) & (freqs <= upper_bound) | (freqs <= -lower_bound) & (freqs >= -upper_bound))
    
#     # 将这些频率的FFT系数设置为零
#     fft_data[idx_band] = 0
    
#     # IFFT转换回时域
#     clean_data = np.fft.ifft(fft_data)
#     return np.real(clean_data).astype(np.int16)

# from scipy.io import wavfile
# from scipy.signal import firwin, lfilter
# # 使用firwin设计带阻滤波器
# lowcut = 1200
# highcut = 1400
# ntaps = 81  # 滤波器的阶数，需要根据实际情况调整
# band_stop_edges = [lowcut, highcut]
# fir_coeff = firwin(ntaps, band_stop_edges, pass_zero=True, window='hamming', fs=RATE)



# from scipy import signal
# from scipy.fftpack import fft,ifft
# import matplotlib.pyplot as plt
# import seaborn
# import numpy as np


# t = np.linspace(0, 1, 1000, False)  # 1 second
# sig = np.sin(2*np.pi*10*t) + np.sin(2*np.pi*20*t)
# fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
# ax1.plot(t, sig)
# ax1.set_title('10 Hz and 20 Hz sinusoids')
# ax1.axis([0, 1, -2, 2])
 
# sos = signal.butter(10, [15,25], 'bp', fs=1000, output='sos')
# filtered = signal.sosfilt(sos, sig)

 
 
 
 
 # 定义音频录制的参数
FORMAT = pyaudio.paInt16  # 数据格式
CHANNELS = 1  # 通道数，这里假设你有6个麦克风
RATE = 48000  # 采样率
CHUNK = 4000  # 每次读取的数据块大小
RECORD_SECONDS = 3  # 录制时间
filename = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/sound_localization/manvoice.wav'


# 初始化PyAudio
p = pyaudio.PyAudio()

# 打开音频流
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=13
                )

print("Recording...")

frames = []

# 开始录制
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    frame = np.frombuffer(data, dtype=np.int16)
    # channel0 = frame[0::CHANNELS]
    # channel2 = frame[1::CHANNELS]
    # frame = remove_noise_freq(frame, 1200, 1400, RATE)
    # frame = remove_noise_freq(frame, 0, 50, RATE)
    frames.append(frame)
allframes = np.concatenate(frames)

# befor_save = lfilter(fir_coeff, 1.0, allframes)  # fir应用滤波器
# print("Finished recording.")
# Save the recorded data as a WAV file
wf = wave.open(filename, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(allframes))
wf.close()

# frameSize, data = wavfile.read(filename)

# aftersave = lfilter(fir_coeff, 1.0, data)
# filtered_samples = lfilter(fir_coeff, 1.0, allframes)
# Save the recorded data as a WAV file
# wf = wave.open(filename, 'wb')
# wf.setnchannels(CHANNELS)
# wf.setsampwidth(p.get_sample_size(FORMAT))
# wf.setframerate(RATE)
# wf.writeframes(b''.join(aftersave))
# wf.close()



# 将捕获的数据转换为NumPy数组
# audio_data = np.stack(frames)

# 创建HDF5文件并写入音频数据
# with h5py.File(filename.replace('wav', 'h5'), 'w') as hf:
#     hf.create_dataset('time_data', data=audio_data)

# print("Data saved to output.h5")

# import tables
# meh5=tables.open_file(filename.replace('wav', 'h5'), mode="w")
# meh5.create_earray('/','time_data', obj=audio_data)
# meh5.set_node_attr('/time_data','sample_freq',16000)
# meh5.close()
# 播放用
# stream.write(audio_data.tobytes())

# 停止和关闭流
stream.stop_stream()
stream.close()
p.terminate()
