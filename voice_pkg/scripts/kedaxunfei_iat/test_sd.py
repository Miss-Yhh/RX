import numpy as np
def sound_energy(frames):
    """计算帧的能量（简单的音量度量）"""
    return np.sqrt(np.mean(frames**2))

def get_mic(savepath):

    # 录音参数设置
    CHANNELS = 1
    RATE = 16000  # 采样率
    # FORMAT = np.int16
    duration = 3  # 录音时间，单位为秒
    # stoptime = 0.8  # 停止时间是0.8秒
    window_duration = 0.5  # 检测窗口的时间长度，单位秒
    threshold = 0.012  # 音量的能量
    window_size = int(RATE * window_duration)  # 窗口大小，以帧为单位
    print("开始录音...")
    wav = np.array([], dtype=np.float32)  # 初始化录音数组

    # 更改默认的输入
    # sd.default.device = 5, None

    step = 0
    total_frames = int(duration / window_duration)
    while step < total_frames:
        step += 1
        frame = sd.rec(window_size, samplerate=RATE, channels=CHANNELS, dtype='float32')
        sd.wait()  # 等待录音完成
        energy = sound_energy(frame)
        print(energy)

        # 一听到有声音,现在的step就重置为0
        if energy > threshold:
            print(f"检测到声音活动继续录")
            step = 0
        wav = np.append(wav, frame)

    micover = True

    print("录音结束。")

    # 保存录音为WAV文件
    # 归一化浮点音频数据到-1到1，然后转换为int16
    wav = np.int16((wav/np.max(np.abs(wav))) * 32767)
    write(savepath, RATE, wav)
    # Save the recorded data as a WAV file
    # wf = wave.open(savepath, 'wb')
    # wf.setnchannels(CHANNELS)
    # wf.setsampwidth(format)
    # wf.setframerate(RATE)
    # wf.writeframes(b''.join(frames))
    # wf.close()
    kedaxunfei_iat(savepath)
