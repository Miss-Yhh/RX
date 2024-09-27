# import pylab as plt
import numpy as np
import pyaudio

nmicro = 6
micros_every_layer = nmicro
R = [0.082, 0.103]

theta_micro = np.zeros(nmicro) # 所有麦克风阵元的角度

for layer in range(1):
    theta_micro[micros_every_layer*layer:micros_every_layer*(layer+1)] = \
        2*np.pi/micros_every_layer*(np.arange(micros_every_layer)+0.5*layer)

# 所有麦克风阵元的坐标
pos = np.stack([
        R[0] * np.cos(theta_micro[:6]), 
        R[0] * np.sin(theta_micro[:6]), 
        np.zeros(6)], axis=1)

'''
	<pos Name="Point 1 " x=" 0.03 " y=" 0.0175 " z=" 0 "/>
	<pos Name="Point 2 " x=" 0 " y=" 0.035 " z=" 0 "/>
	<pos Name="Point 3 " x=" -0.03 " y=" 0.0175 " z=" 0 "/>
	<pos Name="Point 4 " x=" -0.03 " y=" -0.0175 " z=" 0 "/>
	<pos Name="Point 5 " x=" 0 " y=" -0.035 " z=" 0 "/>
	<pos Name="Point 6 " x=" 0.03 " y=" -0.0175 " z=" 0 "/>
'''
pos = np.array([
    [0, -0.035, 0],
    [-0.03, -0.0175, 0],
    [-0.03, 0.0175, 0],
    [0, 0.035, 0],
    [0.03, 0.0175, 0],
    [0.03, -0.0175, 0]
])
# PyAudio的信号采集参数
CHUNK = 3000
FORMAT = pyaudio.paInt16
CHANNELS = 6
RATE = 16000
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                # input_device_index=5
                )



def remove_noise_freq(data, lower_bound, upper_bound, rate):
    # FFT
    fft_data = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(fft_data), 1/rate)
    
    # 找到需要去除的频率范围的索引
    idx_band = np.where((freqs >= lower_bound) & (freqs <= upper_bound) | (freqs <= -lower_bound) & (freqs >= -upper_bound))
    
    # 将这些频率的FFT系数设置为零
    fft_data[idx_band] = 0
    
    # IFFT转换回时域
    clean_data = np.fft.ifft(fft_data)
    return np.real(clean_data).astype(np.int16)


#最后求得的声源位置
xr = 0
yr = 0

#遍历的x和y，假设z为固定深度1m
X_STEP = 10
Y_STEP = 10
x = np.linspace(-0.5, 0.5, X_STEP)
y = np.linspace(-0.5, 0.5, Y_STEP)
z = 0
def beamforming():
    q = list()
    global xr, yr, x, y
    while True:
        data = stream.read(1600, exception_on_overflow=False)
        data = np.frombuffer(data, dtype=np.short)
        
        data = data.reshape(1600, 6)[:,:6].T
        p = np.zeros((x.shape[0], y.shape[0])) # 声强谱矩阵
        volume_norm = np.linalg.norm(data) // 10000
        if volume_norm < 25:
            continue
        # 去除固定频率的声音
        data = remove_noise_freq(data, 1200, 1400, RATE)
        data = remove_noise_freq(data, 20, 100, RATE)

        #傅里叶变换，在频域进行检测
        data_n = np.fft.fft(data)/data.shape[1]# [6,1600]
        data_n = data_n[:, :data.shape[1]//2]
        data_n[:, 1:] *= 2

        # # 获取频率
        # fft = np.fft.fft(data)
        # abs_fft = np.abs(fft)
        # max_freq_index = np.argmax(abs_fft)
        # sample_freq = np.fft.fftfreq(len(data), d=1/RATE)
        # max_freq = sample_freq[max_freq_index]
        # print(f'音频频率: {max_freq} Hz')
        
        # 宽带处理，对于50个不同的频率都进行计算
        
        # r存储每个频率下对应信号的R矩阵
        r = np.zeros((50, nmicro, nmicro), dtype=np.complex_)
        for fi in range(1, 51):
            rr = np.dot(data_n[:, fi*10-10:fi*10+10], data_n[:, fi*10-10:fi*10+10].T.conjugate())/nmicro
            r[fi-1,...] = np.linalg.inv(rr)
        
        # MVDR搜索过程
        for i in range(x.shape[0]):
            for j in range(y.shape[0]):
                dm = np.sqrt(x[i]**2+y[j]**2+z**2)
                delta_dn = pos[:,0]*x[i]/dm + pos[:,1]*y[j]/dm
                for fi in range(1,51):
                    a = np.exp(-1j*2*np.pi*fi*100*delta_dn/340)
                    p[i,j] = p[i,j] + 1/np.abs(np.dot(np.dot(a.conjugate(), r[fi-1]), a))

        xr = np.argmax(p) // Y_STEP
        yr = np.argmax(p) % Y_STEP
        x_loc, y_loc = x[xr], y[yr]
        print(round(x_loc, 2),round(y_loc, 2))
        q.append(x_loc)

        if np.mean(q) < -0.2:
          print('我猜你在我的左边')
        elif np.mean(q) > 0.2:
          print('我猜你在我的右边----')
        if len(q) > 2:
          q = q[1:]
        # # 转为强度0-1
        # p /= np.max(p)
        # # 绘制声强图
        # x1, y1 = np.meshgrid(x,y)
        # ax = plt.axes(projection='3d')
        # ax.plot_surface(x1,y1,np.abs(p.T))
        # plt.pause(0.01)

if __name__ == '__main__':
    while True:
        beamforming()
