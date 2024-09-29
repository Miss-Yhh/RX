import os
from pydub import AudioSegment
from pydub.playback import play
import subprocess
from multiprocessing import Process

def get_audio_length(file_path:str):
    audio = AudioSegment.from_file(file_path)
    length_ms = len(audio)
    return length_ms / 1000.0 

def play_sound(mp3_path:str):
    # play(AudioSegment.from_mp3(mp3_path))   
    #os.system(f"ffplay -nodisp -autoexit {mp3_path}")
    #subprocess.run(["ffplay", "-nodisp", "-autoexit", mp3_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", mp3_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=10 ) # 设置超时为 10 秒

def mp3_to_wav(mp3_path, wav_path):
    os.system(f"ffmpeg -i {mp3_path} -acodec pcm_s16le -ar 16000 -ac 1 -y {wav_path}")

def wav_to_mp3(wav_path, mp3_path):
    os.system(f"ffmpeg -i {wav_path} -acodec libmp3lame -ab 128k -y {mp3_path}")


STATUS_FIRST_FRAME = 0	# 第一帧的标识
STATUS_CONTINUE_FRAME = 1	# 中间帧标识
STATUS_LAST_FRAME = 2	# 最后一帧的标识

flagover = False	# 提示音是否已经读完
micover = False	# False: 还没录音完 True 录音结束
iatover = False	# False: 每次识别结束都会改为True
ifinter = False	# 判断是否打断
text = ''
card_ = 0	# 声卡

now = None

DURATION = 10 # 每 $DURATION 秒录音一次
THRESHOLD_AUDIO = 3 # 音量的能量超过阈值 $THRESHOLD_AUDIO，说明有人说话，继续录音



def get_mic_from_audio(savepath):
    global DURATION  # 全局变量，定义录音持续时间
    global THRESHOLD_AUDIO  # 全局变量，音频的能量阈值（判断有无声音）

    global flagover  # 全局变量，标志音频播放是否结束
    while flagover == False:
        continue  # 如果音频播放未结束，持续等待

    global ifinter  # 全局变量，标志是否中断录音
    ifinter = False

    # 定义音频录制的参数
    FORMAT = pyaudio.paInt16  # 音频数据格式为16位整型
    CHANNELS = 1  # 音频通道数，1表示单声道
    RATE = 48000  # 采样率为48000Hz
    CHUNK = 4000  # 每次读取的音频块大小
    RECORD_SECONDS = DURATION  # 录音持续时间，使用全局变量DURATION

    has_sound = False  # 标志是否检测到有人说话
    # 初始化PyAudio对象
    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording:", end='')
    frames = []  # 存储录制的音频帧
    threshold = THRESHOLD_AUDIO  # 设置音量能量阈值

    # 录音控制参数
    total_valid_frames = 0  # 有效的音频帧数
    somebodytalking_duration = RATE / CHUNK * 0.2  # 人说话的最短持续时间
    stopduration = int(RATE / CHUNK * 0.5)  # 说话后静默持续时间
    bufferlength = int(RATE / CHUNK * 0.5)  # 缓冲区长度
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)  # 录音的总帧数
    step = 0  # 用于控制录音过程的步骤计数

    # 准备音频帧的buffer
    audio_q = queue.deque()  # 用于存储录音前的缓冲帧
    str2terminal = queue.deque(['-'] * 19)  # 用于在终端显示录音状态

    while step < total_frames:
        if ifinter:  # 如果录音中断，直接返回
            return ''
        
        step += 1  # 增加步数
        data = stream.read(CHUNK)  # 读取音频数据
        frame = np.frombuffer(data, dtype=np.int16)  # 将音频数据转换为numpy数组
        energy = np.linalg.norm(frame) // 10000  # 计算音频帧的能量

        # 如果检测到声音，或者已经开始录制，则将帧加入frames
        if energy > threshold or len(frames) > 0:
            frames.append(frame)

        # 如果没有声音，则将帧存入缓冲区
        if len(frames) == 0:
            audio_q.append(frame)
            if len(audio_q) > bufferlength:
                audio_q.popleft()  # 保持缓冲区长度固定

        # 如果检测到声音，重置静默时间
        if energy > threshold:
            total_valid_frames += 1
            if not has_sound and total_valid_frames > somebodytalking_duration:
                has_sound = True  # 检测到持续说话，标志位设为True

            str2terminal.append('+')  # 在终端显示+号表示检测到声音
            str2terminal.popleft()

            # 重置录音步数和静默帧数
            step = 0
            aftersound_frames = stopduration
        else:
            str2terminal.append('-')  # 在终端显示-号表示未检测到声音
            str2terminal.popleft()

        print("\r" + "".join(str2terminal), end='')

        # 如果进入静默状态，计算是否超过静默时间
        if energy <= threshold and has_sound:
            aftersound_frames -= 1
            if aftersound_frames < 0:
                break  # 如果静默时间超过设定值，停止录音

    print("录音结束。")

    # 停止和关闭音频流
    stream.stop_stream()
    stream.close()
    p.terminate()

    if len(frames) == 0:
        return None  # 如果没有有效音频帧，返回None

    # 将录制的音频数据保存为WAV文件
    wf = wave.open(savepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(list(audio_q) + frames))  # 将缓冲区和有效帧写入文件
    wf.close()

    # 使用FFmpeg将音频文件转换为16kHz采样率
    savepath_new = savepath.replace(".wav", "16k.wav")
    cmd = " ".join(['ffmpeg', '-loglevel quiet', '-i', savepath, '-ar', '16000', '-y', savepath_new])
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    code = process.wait()  # 等待FFmpeg转换完成


if __name__ == "__main__":
    # wav_to_mp3("please_say.wav", "please_say.mp3")
    # wav_to_mp3("finish_instruction.wav", "finish_instruction.mp3")
    play_sound("/home/hit/RX/save_waves/finish_instruction.mp3")