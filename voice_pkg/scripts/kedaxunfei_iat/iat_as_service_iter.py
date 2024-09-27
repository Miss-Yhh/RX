#!/home/lemon/anaconda3/envs/zt/bin/python
# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下，您可自行逐一或者复制到一个新的txt文件利用pip一次性安装：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#
#  语音听写流式 WebAPI 接口调用示例 接口文档（必看）：https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
#  webapi 听写服务参考帖子（必看）：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947&extra=
#  语音听写流式WebAPI 服务，热词使用方式：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--个性化热词，
#  设置热词
#  注意：热词只能在识别的时候会增加热词的识别权重，需要注意的是增加相应词条的识别率，但并不是绝对的，具体效果以您测试为准。
#  语音听写流式WebAPI 服务，方言试用方法：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--识别语种列表
#  可添加语种或方言，添加后会显示该方言的参数值
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import os
import wave
import websocket
import datetime
import shutil
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
# import speech_recognition as sr 
# pip install SpeechRecognition

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models

from pydub.playback import play
from pydub import AudioSegment


STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

flagover = False  # 提示音是否已经读完
micover = False  # False: 还没录音完 True 录音结束
iatover = False  # False: 每次识别结束都会改为True
text = ''
card_ = 0  # 声卡

now = None
environment = 'default'

DURATION = 2 # 每 $DURATION 秒录音一次
THRESHOLD_AUDIO = 3 # 音量的能量超过阈值 $THRESHOLD_AUDIO，说明有人说话，继续录音

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile
        self.result = ''

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":0,"vad_eos":10000,"dwa":"wpgs"}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        return url

def kedaxunfei_iat_service(savepath):
    global iatover
    iatover = False
    time1 = datetime.now()
    def on_message(ws, message):
        try:
            code = json.loads(message)["code"]
            sid = json.loads(message)["sid"]
            if code != 0:
                errMsg = json.loads(message)["message"]
                print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            else:
                data = json.loads(message)["data"]["result"]["ws"]
                iflast = json.loads(message)["data"]["result"]["ls"]
                pgs = json.loads(message)["data"]["result"]["pgs"]
                result = ""
                for i in data:
                    for w in i["cw"]:
                        result += w["w"]
                if pgs == 'rpl':
                    wsParam.result = result
                else:
                    wsParam.result += result
                print(wsParam.result)
                if iflast:
                    ws.close()
        except Exception as e:
            print("receive msg,but parse exception:", e, datetime.now())
            ws.close()
            return



    # 收到websocket错误的处理
    def on_error(ws, error):
        print("### error:", error, datetime.now())
        ws.close()


    # 收到websocket关闭的处理
    def on_close(ws,a,b):
        print("### closed ###", datetime.now())
        print(a)
        print(b)


    # 收到websocket连接建立的处理
    def on_open(ws):
        def run(*args):
            frameSize = 3000  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

            # sound = AudioSegment.from_file(wsParam.AudioFile, "wav") #加载WAV文件
            # sound = sound.apply_gain(20)
            # sound.export(wsParam.AudioFile, format="wav")
            with open(wsParam.AudioFile, "rb") as fp:
                print('start audio')
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = STATUS_LAST_FRAME
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == STATUS_FIRST_FRAME:
                        d = {"common": wsParam.CommonArgs,
                                "business": wsParam.BusinessArgs,
                                "data": {"status": 0, "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), 'utf-8'),
                                        "encoding": "raw"}}
                        d = json.dumps(d)
                        print('send first audio')
                        ws.send(d)
                        status = STATUS_CONTINUE_FRAME
                    # 中间帧处理
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), 'utf-8'),
                                        "encoding": "raw"}}
                        # print('send mid audio')
                        ws.send(json.dumps(d))
                    # 最后一帧处理
                    elif status == STATUS_LAST_FRAME:
                        d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), 'utf-8'),
                                        "encoding": "raw"}}
                        print('send last audio')
                        ws.send(json.dumps(d))
                        time.sleep(1)
                        break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
                ws.close()
        time1 = datetime.now()
        thread.start_new_thread(run, ())
        time2 = datetime.now()
        print('speechrecognition cost = ', time2 - time1)


    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    APPID, APISecret, APIKey = config['kedaxunfei_appid'], config['kedaxunfei_apiSecret'], config['kedaxunfei_appkey']
    wsParam = Ws_Param(APPID=APPID, APISecret=APISecret,
                       APIKey=APIKey,
                       AudioFile=savepath)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    print(f"socket time cost final:{datetime.now()-time1}")
    
    print(wsParam.result)
    res = wsParam.result
    global text 
    if res is None:
        text = ''        
    elif (isinstance(res, str) or isinstance(res, list)) and len(res) < 1:
        text = ''        
    else:
        text = wsParam.result

        # 保存数据
        global now
        global environment
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d-%H%M%S')
        copy_path = f'/home/kuavo/catkin_dt/src/voice_pkg/scripts/voice_text_datasets/{environment}/{date_str}.wav'
        copy_dir = os.path.dirname(copy_path)
        os.makedirs(copy_dir, exist_ok=True)
        shutil.copyfile(savepath, copy_path)
        txt_filename = f'/home/kuavo/catkin_dt/src/voice_pkg/scripts/voice_text_datasets/{environment}.txt'
        txt_content = f'/{environment}/{date_str}.wav: {text}\n' # 使用“: ”作为分隔符
        with open(txt_filename, 'a') as file:
            file.write(txt_content)
        
    iatover = True
    print('-------iat is over----------')

def tencentcloud_iat(savepath):
    with open(savepath, "rb") as fp:
        data = fp.read()
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    SecretId, SecretKey = config['tencentcloud_SecretId'], config['tencentcloud_SecretKey']
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(SecretId, SecretKey)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "asr.ap-beijing.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = asr_client.AsrClient(cred, "", clientProfile)
        # client = asr_client.AsrClient(cred, "")

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.SentenceRecognitionRequest()
        params = {
            "EngSerViceType": "16k_zh",
            "SourceType": 1,
            "VoiceFormat": "wav",
            "Data":base64.b64encode(data).decode(encoding='utf-8'),
            "DataLen": len(data),
            "WordInfo": 2
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个SentenceRecognitionResponse的实例，与请求对象对应
        resp = client.SentenceRecognition(req)
        # 输出json格式的字符串回包
        return resp.Result

    except TencentCloudSDKException as err:
        print(err)

def run_prompt_audio(filename):
    global card_
    # play(AudioSegment.from_mp3(filename))
    cmd = f"aplay -D plughw:{card_},0 {filename}"
    exit_status = os.system(cmd)
    global flagover
    flagover = True

import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
def sound_energy(frames):
    """计算帧的能量（简单的音量度量）"""
    return np.sqrt(np.mean(frames**2))
def get_mic(savepath):
    global flagover
    while flagover == False: continue

    global micover

    global DURATION

    # 录音参数设置
    CHANNELS = 1
    RATE = 16000  # 采样率
    # FORMAT = np.int16
    duration = DURATION  # 录音时间，单位为秒
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
        # print(energy)

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
    kedaxunfei_iat_service(savepath)

import wave
import pyaudio
import numpy as np
import subprocess

def get_mic_from_audio(savepath, haode_audio_path):
    global flagover
    while flagover == False: continue

    global micover
    
    global DURATION
    global THRESHOLD_AUDIO
 
    # 定义音频录制的参数
    FORMAT = pyaudio.paInt16  # 数据格式
    CHANNELS = 1  # 通道数，这里假设你有6个麦克风
    RATE = 48000  # 采样率
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
                    # input_device_index=6
                    )

    print("Recording...")
    frames = []
    threshold = THRESHOLD_AUDIO  # 音量的能量
    # 开始录制
    total_valid_frames = 0
    somebodytalking_duration = RATE / CHUNK * 0.8
    stopduration = int(RATE / CHUNK * 0.8)
    has_sound = False
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)
    print(total_frames)
    step = 0
    while step < total_frames:
        step += 1
        data = stream.read(CHUNK)
        frame = np.frombuffer(data, dtype=np.int16)
        frames.append(frame)
        energy = np.linalg.norm(frame) // 10000
        # print(energy)

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
    wf.writeframes(b''.join(frames))
    wf.close()

    # subprocess.run(['ffmpeg','-i', savepath,'-ac','pan=6c|c0=2*c0|c1=0.1*c1|c2=0.1*c2|c3=0.1*c3|c4=0.1*c4|c5=0.1*c5', '-y', savepath])
    
    # 修改为16k
    savepath_new = savepath.replace(".wav", "16k.wav")
    cmd = " ".join(['ffmpeg', '-loglevel quiet', '-i', savepath,'-ar','16000', '-y', savepath_new])
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    code = process.wait()
    # subprocess.run(['ffmpeg','-i',savepath,'-ac','1', '-y', savepath])

    micover = True

    kedaxunfei_iat_service(savepath_new)


# def mic_iat(savepath):
#     # 打开麦克风录音
#     r = sr.Recognizer()
#     global flagover
#     global micover
#     r.pause_threshold = 0.8   # minimum length of silence (in seconds) that will register as the end of a phrase.  
#     r.energy_threshold = 4000
#     # with sr.Microphone() as source1:
#     #     # calibrate ambient noise
#     #     r.adjust_for_ambient_noise(source1, duration=0.8)
#     # print(r.energy_threshold)
#     # time1 = datetime.now()
#     try:
#         with sr.Microphone() as source:
#             # run iam here
#             # input()
#             while flagover == False: continue
#             time1 = datetime.now()
#             # r.listen start recording when there is audio input higher than threshold (set this to a reasonable number),
#             # and stops recording when silence >0.8s(changable)
#             print("I am listening....", datetime.now())
#             audio = r.listen(source, timeout=2, phrase_time_limit=15)
#             # audio = r.listen(source, timeout=2, phrase_time_limit=2)
#             print("I finish listening....", datetime.now())
            
#             time1 = datetime.now()
#             # get wav data from AudioData object 
#             wav = audio.get_wav_data(convert_rate=16000, convert_width=2) # width=2 gives 16bit audio.
            
#             # # 保存 wav
#             # write audio to a RAW file
#             # with open(wsParam.AudioFile, "wb") as f:
#             #     f.write(audio.get_raw_data())

            
#             print('----+-', savepath)
#             wf = wave.open(savepath, 'wb')
#             wf.setnchannels(1)
#             wf.setsampwidth(2)
#             wf.setframerate(16000)
#             wf.writeframes(wav)
#             wf.close()
#             print('sr is over', datetime.now() - time1)
#             micover = True
#     except sr.exceptions.WaitTimeoutError as e:
#         print('wmjjjjj', e)
#         micover = True
#         return
    
#     kedaxunfei_iat_service(savepath)
  
def iat_web_api(input, iter=1, environment_name='default', card=2):
    # 测试时候在此处正确填写相关信息即可运行
    global micover
    global iatover
    global text
    global environment

    # 重置全局变量
    global card_
    card_ = card
    text = ''
    micover = False
    iatover = False
    environment = environment_name

    if input == 'zai':
        filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere_cut.wav'
    else:
        filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/ding_cut.wav'
    thread.start_new_thread(run_prompt_audio, (filename,))
    haode_audio_path = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech/hao_de__wo_ting_dao_le__pcm.wav'
    for i in range(iter):
        print(f'第{i}次')

        # 在文件名中加入时间信息
        
        savepath_temp = f"/home/kuavo/catkin_dt/src/voice_pkg/temp_record/mic_z_{i}.wav"

        thread.start_new_thread(get_mic_from_audio, (savepath_temp, haode_audio_path))
        while not micover:
            if text != '':
                break
            else:
                continue
        if text != '':
            break
        micover = False
    if text == '':
        # 如果挑出循环的时候是空的，等待最后一次的识别返回
        while iatover == False:
            continue

    return text

if __name__ == "__main__":
    '''
    需要修改
      1. run_prompt_audio中 提示音的文件路径
      2. 录音文件的文件路径
    参数解读
      1. iter  每次  两秒  
      2. 只有一开始会有 叮 或 我在
    '''
    
    # flagover = True
    # for i in range(10):
    #   input()
    #   savepath = f'/home/kuavo/catkin_dt/src/voice_pkg/temp_record/mic2tree_{i}.wav'
    #   get_mic_from_audio(savepath)
    res = iat_web_api(input='ding', iter=3, card=0)
    print('res = ', res)
    # # flagover = True
    # kedaxunfei_iat_service(savepath='/home/kuavo/catkin_dt/src/voice_pkg/temp_record/mic_z_0_16000.wav')
