datapath = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/sound_localization/manvoice5.wav'
import numpy as np
from scipy.signal import firwin, lfilter
from scipy.io import wavfile
# 使用firwin设计带阻滤波器
lowcut = 1200
highcut = 1400
RATE = 16000
ntaps = 81  # 滤波器的阶数，需要根据实际情况调整
band_stop_edges = [lowcut, highcut]
fir_coeff = firwin(ntaps, band_stop_edges, pass_zero=True, window='hamming', fs=RATE)

frameSize, data = wavfile.read(datapath)

filtered_samples = lfilter(fir_coeff, 1.0, data)

wavfile.write(datapath, frameSize, filtered_samples.astype(np.int16))