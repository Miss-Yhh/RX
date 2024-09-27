import os
import sys
import wave
import pypinyin
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

# flagover = False  # 提示音是否已经读完
# micover = False  # False: 还没录音完 True 录音结束
# iatover = False  # False: 每次识别结束都会改为True
text = ''
card_ = 0  # 声卡

now = None
environment = 'default'

DURATION = 4 # 每 $DURATION 秒录音一次
THRESHOLD_AUDIO = 5 # 音量的能量超过阈值 $THRESHOLD_AUDIO，说明有人说话，继续录音

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

import re
def filter_letters(input_string):
    # 使用列表推导式过滤出仅包含字母的字符
    filtered_string = ''.join(re.findall(r'[A-Za-z0-9]', input_string))
    return filtered_string

def kedaxunfei_iat_service(savepath, timestamp):
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
    if res != '' and res != None:
        with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_iat/audiotext4finetune/textpath.json', 'r+', encoding='utf-8') as fj:
            jsondata = json.load(fj)
            # 最后再将生成好的音频文件保存起来
            jsondata[timestamp].append(savepath)
            jsondata[timestamp].append(res)
            fj.seek(0)
            json.dump(jsondata, fj, ensure_ascii=False)
        return True
    else:
        return False




import wave
import pyaudio
import numpy as np
import subprocess

def get_mic_from_audio(savepath):
    global DURATION
 
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
    # 开始录制
    total_frames = int(RATE / CHUNK * RECORD_SECONDS)
    print(total_frames)
    step = 0
    while step < total_frames:
        step += 1
        data = stream.read(CHUNK)
        frame = np.frombuffer(data, dtype=np.int16)
        frames.append(frame)
        energy = np.linalg.norm(frame) // 10000
        print('\r'+'_'*step, end='')
        
        if step % (RATE // CHUNK) == 0:
            # print(step // (RATE // CHUNK))
            pass

        # 一听到有声音,现在的step就重置为0
        # if flag == False:
            # break
    
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
    # savepath_new = savepath.replace(".wav", "_16k.wav")
    # cmd = " ".join(['ffmpeg','-i', savepath,'-ar','16000', '-y', savepath_new])
    # process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # code = process.wait()

    # # 删掉48k
    # os.system(f"rm {savepath}")
    # subprocess.run(['ffmpeg','-i',savepath,'-ac','1', '-y', savepath])


    # res = kedaxunfei_iat_service(savepath_new, timestamp)
    # print(res)
if __name__ == '__main__':
    # savepath = sys.argv[1]
    savepath = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/test0514.wav'
    # timestamp = sys.argv[2]
    
    get_mic_from_audio(savepath)