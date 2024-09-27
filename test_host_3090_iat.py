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
import queue
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

# from tencentcloud.common import credential
# from tencentcloud.common.profile.client_profile import ClientProfile
# from tencentcloud.common.profile.http_profile import HttpProfile
# from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# from tencentcloud.asr.v20190614 import asr_client, models

# from pydub.playback import play
# from pydub import AudioSegment

import rospy


STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

flagover = False  # 提示音是否已经读完
micover = False  # False: 还没录音完 True 录音结束
iatover = False  # False: 每次识别结束都会改为True
ifinter = False  # 判断是否打断
text = ''
card_ = 0  # 声卡

now = None

DURATION = 10 # 每 $DURATION 秒录音一次
THRESHOLD_AUDIO = 3 # 音量的能量超过阈值 $THRESHOLD_AUDIO，说明有人说话，继续录音


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey=None, APISecret=None, AudioFile=''):
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
        # url = 'wss://ws-api.xfyun.cn/v2/iat'
        # url = 'ws://103.8.34.136:26002/createRec'
        url = 'ws://192.168.50.14:26002/createRec'
        print(url)
        # url = 'ws://127.0.0.1:26002/createRec'
        # 生成RFC1123格式的时间戳
        # now = datetime.now()
        # date = format_date_time(mktime(now.timetuple()))

        # # 拼接字符串
        # signature_origin = "host: " + "192.168.31.90" + "\n"
        # signature_origin += "date: " + date + "\n"
        # signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # # 进行hmac-sha256进行加密
        # signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
        #                          digestmod=hashlib.sha256).digest()
        # signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        # authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        #     self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        # authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # # 将请求的鉴权参数组合为字典
        # v = {
        #     "authorization": authorization,
        #     "date": date,
        #     "host": "192.168.31.90"
        # }
        # # 拼接鉴权参数，生成url
        # url = url + '?' + urlencode(v)
        return url

def kedaxunfei_iat_service(savepath):
    time1 = datetime.now()
    def on_message(ws, message):
        try:
            code = json.loads(message)["code"]
            # sid = json.loads(message)["sid"]
            iflast = False
            if code != 0:
                errMsg = json.loads(message)["desc"]
                print("sid:%s call error:%s code is:%s" % (errMsg, code))
                iflast = True
            else:
                result = json.loads(json.loads(message)["result"])[0]
                iflast = result["last"]
                data = json.loads(result['data'])
                for w in data['ws']:
                    res = w['cw'][0]['w']
                    wsParam.result += res
            if iflast:
                # print("ws is closed")
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
        # pass
        print("### closed ###", datetime.now())
        print(a)
        print(b)


    # 收到websocket连接建立的处理
    def on_open(ws):
        def run(*args):
            frameSize = 80000  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

            # sound = AudioSegment.from_file(wsParam.AudioFile, "wav") #加载WAV文件
            # sound = sound.apply_gain(20)
            # sound.export(wsParam.AudioFile, format="wav")
            with open(wsParam.AudioFile, "rb") as fp:
                # print('start audio')
                sessionId = format_date_time(mktime(datetime.now().timetuple()))
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = STATUS_LAST_FRAME
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == STATUS_FIRST_FRAME:
                        resetFlag = True
                        endFlag = False
                        # print('send first audio')
                        status = STATUS_CONTINUE_FRAME
                    elif status == STATUS_CONTINUE_FRAME:
                        resetFlag = False
                        endFlag = False
                        # print('send rest audio')
                    else:
                        resetFlag = False
                        endFlag = True
                        # print('send last frame')
                    d = {
                        "sessionParams":{
                            "traceId":"tur1715746708801",
                            "reset":resetFlag,
                            "id":"tur1715746708801",
                            "abilityList":[
                                {"param":"{\"aue\":\"raw\",\"rst\":\"json\",\"engine_param\":\"pproc_param_puncproc=false\",\"eos\":100000,\"sid\":\"tur1715746708801\"}","abilityCode":"iat","serviceName":"iat"}
                            ],
                            "abilityParams":{
                                "iat":{
                                    "wbest":0,
                                    "rst":"json",
                                    "eos":100000,
                                    "endFlag":'true' if endFlag else 'false',
                                    "dwa":"wpgs",
                                    "sid":"tur1715746708801"
                                }
                            }
                        },
                        "debug":True,
                        "data":str(base64.b64encode(buf), 'utf-8'),
                        "appid":"ef014ded",
                        "scene":"main_box"
                    }

                    d = json.dumps(d)
                    ws.send(d)
                    if status == STATUS_LAST_FRAME:
                        time.sleep(1)  # 不能太早关闭ws，否则没有返回
                        break
                    # if status == STATUS_FIRST_FRAME:
                    #     d = {"common": wsParam.CommonArgs,
                    #             "business": wsParam.BusinessArgs,
                    #             "data": {"status": 0, "format": "audio/L16;rate=16000",
                    #                     "audio": str(base64.b64encode(buf), 'utf-8'),
                    #                     "encoding": "raw"}}
                    #     d = json.dumps(d)
                    #     print('send first audio')
                    #     ws.send(d)
                    #     status = STATUS_CONTINUE_FRAME
                    # # 中间帧处理
                    # elif status == STATUS_CONTINUE_FRAME:
                    #     d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                    #                     "audio": str(base64.b64encode(buf), 'utf-8'),
                    #                     "encoding": "raw"}}
                    #     # print('send mid audio')
                    #     ws.send(json.dumps(d))
                    # # 最后一帧处理
                    # elif status == STATUS_LAST_FRAME:
                    #     d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                    #                     "audio": str(base64.b64encode(buf), 'utf-8'),
                    #                     "encoding": "raw"}}
                    #     print('send last audio')
                    #     ws.send(json.dumps(d))
                    #     time.sleep(1)
                    #     break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
                ws.close()
        time1 = datetime.now()
        print("open here 1")
        thread.start_new_thread(run, ())
        time2 = datetime.now()
        # print('speechrecognition cost = ', time2 - time1)


    with open('../config_dt.json', 'r') as fj:
        config = json.load(fj)
    APPID, APISecret, APIKey = config['kedaxunfei_appid'], config['kedaxunfei_apiSecret'], config['kedaxunfei_appkey']
    wsParam = Ws_Param(APPID=APPID, 
                       APISecret=APISecret,
                       APIKey=APIKey,
                       AudioFile=savepath)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    print(wsUrl)
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    print("DEBUG hsong 1")
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    # print(f"socket time cost final:{datetime.now()-time1}")
    print("DEBUG hsong 2")
    print(wsParam.result)
    print('-------iat is over----------')
    return wsParam.result

def run_prompt_audio(filename):
    global card_
    # play(AudioSegment.from_wav(filename))
    print(card_)
    print(111111)
    print(filename)
    cmd = f"aplay -D plughw: {card_}, 0 {filename} > /dev/null 2 > &1"
    exit_status = os.system(cmd)
    global flagover
    flagover = True

import wave
import pyaudio
import numpy as np
import subprocess

def get_mic_from_audio(savepath):
    """
        从大声开始录音，保存到savepath
        hsong
    """

    global DURATION
    global THRESHOLD_AUDIO
    
    global flagover
    while flagover == False: continue
    global ifinter
    ifinter = False

 
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

    print("Recording:", end='')
    frames = []
    threshold = THRESHOLD_AUDIO  # 音量的能量
    # 开始录制
    total_valid_frames = 0
    somebodytalking_duration = RATE / CHUNK * 0.2
    stopduration = int(RATE / CHUNK * 1.5)
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
        energy = np.linalg.norm(frame) // 10000
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
    
    return kedaxunfei_iat_service(savepath_new)

from std_msgs.msg import String
def ivw_callback(data):
  # rospy.loginfo(rospy.get_caller_id() + "I heard %s from ivw", data.data)
  print(f"收到打断信号！现在可以打断", datetime.now())
  global ifinter
  ifinter = True

def iat_web_api(input, iter=1, environment_name='default', card=2):
    """
    param
        input: str
        iter: 没用
        environment_name：没用
        card：定义播音的声卡（喇叭）
        
        还需要修改录音的音频文件wav的路径 savepath_temp = f"/home/robot/catkin_dt/src/voice_pkg/temp_record/mic_z_0.wav"
        还需要修改提示音文件的路径： 我在 = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere_cut.wav'
        还需要修改提示音文件的路径： 叮 = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere_cut.wav'

        还需要根据录音设备修改录音的硬件参数
        RATE = 48000  # 采样率

    """
    # 测试时候在此处正确填写相关信息即可运行
    ivw_sub = rospy.Subscriber("ivw_chatter", String, ivw_callback) # 订阅ivw话题，唤醒词

    # 重置全局变量
    global card_
    card_ = card
    text = ''

    if input == 'zai':
        filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere_cut.wav'
    else:
        filename = '/home/hit/RX/temp_record'
    print("DEBUG 33")
    thread.start_new_thread(run_prompt_audio, (filename,))
    # haode_audio_path = '/home/robot/catkin_dt/src/voice_pkg/temp_record/text2speech/hao_de__pcm.wav'
    savepath_temp = f"/home/hit/RX/temp_record/record_TMP.mp3"

    text = get_mic_from_audio(savepath_temp)
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
    #res = iat_web_api(input='ding', iter=1, card=1)
    #print('res1 = ', res)
    time1 = datetime.now()
    kedaxunfei_iat_service('/home/hit/RX/temp_record/record_2.mp3')
    time2 = datetime.now()
    # print(time2-time1)
    a = {
        "sessionParams":{
            "traceId":"tur1715746708801",
            "reset":False,
            "id":"tur1715746708801",
            "abilityList":[
                {"param":"{\"aue\":\"raw\",\"rst\":\"json\",\"engine_param\":\"pproc_param_puncproc=false\",\"eos\":100000,\"sid\":\"tur1715746708801\"}","abilityCode":"iat","serviceName":"iat"}
                ],
            "abilityParams":{
                "iat":{
                    "wbest":0,
                    "rst":"json",
                    "eos":100000,
                    "endFlag":"false",
                    "dwa":"wpgs",
                    "sid":"tur1715746708801"
                }
            }
        },
        "debug":True,
        "data":"",
        "appid":"ef014ded",
        "scene":"main_box"
    }