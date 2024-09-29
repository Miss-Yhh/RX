import pyaudio
import wave
import numpy as np
import queue
import subprocess
from utils import play_sound  
DURATION=15                  # 无人说话时每轮录音的时间
THRESHOLD_AUDIO=25 #声音检测的中断阈值

def get_mic_from_audio(savepath):
    play_sound('/home/hit/RX/save_waves/please_say.mp3')
    global DURATION  # 录音时长，单位为秒
    global THRESHOLD_AUDIO  # 音量阈值

    global ifinter  # 中断标志
    ifinter = False

    # 定义音频录制的参数
    FORMAT = pyaudio.paInt16  # 音频格式为16位整型
    CHANNELS = 1  # 单声道
    RATE = 16000  # 采样率为48kHz
    CHUNK = 4000  # 每次读取4000个音频数据点
    RECORD_SECONDS = DURATION  # 录制时长

    has_sound = False  # 用于判断是否检测到声音
    CHUNK_1 = CHUNK // 4
    p = pyaudio.PyAudio()  # 初始化 PyAudio


    # 打开音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print("Pre-reading to clear buffer...")

    frames = []  # 存储音频帧
    threshold = THRESHOLD_AUDIO  # 定义音量阈值
    total_valid_frames = 0  # 记录有效音频帧数
    somebodytalking_duration = RATE / CHUNK * 0.2  # 检测到有人说话的时长
    stopduration = int(RATE / CHUNK * 0.5)  # 静音时长判断
    bufferlength = int(RATE / CHUNK * 0.5)  # 缓冲队列长度
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)  # 总帧数
    step = 0  # 当前的帧计数器

    # 准备音频frame的缓冲队列
    print(2)
    audio_q = queue.deque()
    str2terminal = queue.deque()
    for i in range(19):
        str2terminal.append('-')  # 初始状态显示为静音
    print(3)

    # 录音循环
    while step < total_frames:
        print(4)
        if ifinter:  # 如果中断标志为 True，停止录音
            return ''
        step += 1
        data = stream.read(CHUNK)  # 读取一块音频数据
        frame = np.frombuffer(data, dtype=np.int16)  # 转换为整数数组
        energy = np.linalg.norm(frame) // 10000  # 计算音频能量

        print(energy)
        # 如果能量超过阈值，或者已经开始录音，保存该帧
        if energy > threshold or len(frames) > 0:
            frames.append(frame)

        # 保持静音帧进入缓冲队列
        if len(frames) == 0:
            audio_q.append(frame)
            if len(audio_q) > bufferlength:
                audio_q.popleft()

        # 检测到声音，重置静默时间
        if energy > threshold:
            print(6)
            total_valid_frames += 1
            if has_sound == False and total_valid_frames > somebodytalking_duration:
                has_sound = True  # 确认有人在说话
            str2terminal.append('+')  # 显示有声音
            str2terminal.popleft()
            step = 0  # 重置帧计数
            aftersound_frames = stopduration  # 重置静音帧计数
        else:
            print(5)
            str2terminal.append('-')  # 显示静音状态
            str2terminal.popleft()

        print("\r" + "".join(str2terminal), end='')

        # 当静音超过阈值时，停止录音
        if energy <= threshold and has_sound == True:
            aftersound_frames -= 1
            if aftersound_frames < 0:
                break

    print("录音结束。")

    # 停止音频流并关闭
    stream.stop_stream()
    stream.close()
    p.terminate()

    if len(frames) == 0:
        print(8)
        return None  # 如果没有有效的录音数据，返回 None

    # 保存音频数据到指定路径
    wf = wave.open(savepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(list(audio_q) + frames))  # 将缓冲区和录音数据写入文件
    wf.close()

    print(f"音频文件已保存到 {savepath}")

    return savepath  # 返回保存的音频文件路径


# path='/home/hit/RX/voice_pkg/scripts/1.mp3'
# get_mic_from_audio(path)





def get_mic_from_audio(savepath):
	global DURATION
	global THRESHOLD_AUDIO
		

	global ifinter
	ifinter = False

 
	# 定义音频录制的参数
	FORMAT = pyaudio.paInt16	# 数据格式
	CHANNELS = 1	# 通道数，这里假设你有6个麦克风
	RATE = 16000	# 采样率
	CHUNK = 4000	# 每次读取的数据块大小
	RECORD_SECONDS = DURATION	# 录制时间
		
	has_sound = False	# 是否有人在说话
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

	print("Recording:", end='')
	frames = []
	threshold = THRESHOLD_AUDIO	# 音量的能量
	# 开始录制
	total_valid_frames = 0
	somebodytalking_duration = RATE / CHUNK * 0.2
	stopduration = int(RATE / CHUNK * 0.5)
	bufferlength = int(RATE / CHUNK * 0.5)
	total_frames = int(RATE / CHUNK * RECORD_SECONDS)
	# print(total_frames)
	step = 0
		
	# 准备音频frame的buffer
	audio_q = queue.deque()
	str2terminal = queue.deque()
	for i in range(19):
		str2terminal.append('-')
	while step < total_frames:
		if ifinter:
			return ''
		step += 1
		data = stream.read(CHUNK)
		frame = np.frombuffer(data, dtype=np.int16)
		energy = np.linalg.norm(frame) // 1000
		# print(energy)
		
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
			str2terminal.append('+')
			str2terminal.popleft()
			# 持续录制，不会停止
			step = 0
			# 防止说话到一半有继续说，此时应当保证静默时间 仍然是从0.8秒开始减
			aftersound_frames = stopduration
		else:
			str2terminal.append('-')
			str2terminal.popleft()
		print("\r"+"".join(str2terminal), end='')
		# 一旦不再听到声音了，就计算是否到了静默时间
		if energy <= threshold and has_sound == True:
			aftersound_frames -= 1
			if aftersound_frames < 0:
				# 如果说话之后的静默时间超过一秒
				# print('break ---')
				# thread.start_new_thread(run_prompt_audio, (haode_audio_path,))
				break
		
	print("录音结束。")


	# 停止和关闭流
	stream.stop_stream()
	stream.close()
	p.terminate()
	
	if len(frames) == 0:
		return None
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
	
	return True  # 修正缩进错误