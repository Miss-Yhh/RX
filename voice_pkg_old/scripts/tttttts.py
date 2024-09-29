#!/usr/bin/env python3
import subprocess
import wave
import websocket
import datetime
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
import os
import sys

from pydub.playback import play
from pydub import AudioSegment
import pypinyin

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

playstate = 'stop'
lastproc = None  # 用于异步播放进程管理

# Ws_Param类，用于构建WebSocket参数
class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, textinput):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = textinput
        self.allaudio = b''

    # 生成 WebSocket 连接的 URL
    def create_url(self):
        # 返回你要连接的 WebSocket 地址
        url = 'ws://192.168.31.90:26002/createRec'
        return url


# TTS 功能，输入文本并生成音频文件保存到savepath
def get_tts(textinput, savepath):
    def on_message(ws, message):
        try:
            message = json.loads(message)
            code = message["code"]
            sid = message["sid"]
            iflast = False
            if code != 0:
                errMsg = json.loads(message)["desc"]
                print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
                iflast = True
            else:
                result = json.loads(message["result"])[0]
                if result is None:
                    print('发现空的！！！！')
                    return
                audio = result["data"]
                audio = base64.b64decode(audio)
                wsParam.allaudio += audio
                iflast = result['last']
            if iflast:
                print("WebSocket 连接关闭")
                # 保存音频到 WAV 文件
                wf = wave.open(savepath, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(wsParam.allaudio)
                wf.close()
                ws.close()

        except Exception as e:
            print("接收消息解析失败:", e, datetime.now())
            ws.close()

    def on_error(ws, error):
        print("### 错误:", error, datetime.now())

    def on_close(ws, a, b):
        print("### WebSocket 关闭 ###", datetime.now())

    def on_open(ws):
        def run(*args):
            d = {
                "sessionParams": {
                    "traceId": "tur1715748522354",
                    "reset": True,
                    "id": "tur1715748522354",
                    "abilityList": [{
                        "param": "{\"volume\":20,\"native_voice_name\":\"yezi\",\"sample_rate\":\"16000\",\"audio_coding\":\"raw\",\"endFlag\":\"true\",\"pitch\":50,\"speed\":35}",
                        "abilityCode": "tts",
                        "serviceName": "tts"
                    }]
                },
                "debug": True,
                "data": str(base64.b64encode(wsParam.Text.encode("utf-8")), 'utf-8'),
                "appid": "ef014ded",
                "firstAi": "tts",
                "scene": "main_box"
            }
            d = json.dumps(d)
            ws.send(d)
            if os.path.exists(savepath):
                os.remove(savepath)

        thread.start_new_thread(run, ())

    with open('/home/robot/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    APPID, APISecret, APIKey = config['kedaxunfei_appid'], config['kedaxunfei_apiSecret'], config['kedaxunfei_appkey']
    wsParam = Ws_Param(APPID=APPID, APISecret=APISecret, APIKey=APIKey, textinput=textinput)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


# 播放 TTS 音频文件的函数
def tts_playsound(input, index=1000):
    def playsound_work(savepath):
        global playstate
        playstate = 'playing'
        play(AudioSegment.from_wav(savepath))
        playstate = 'stop'

    with open('/home/robot/catkin_dt/src/voice_pkg/temp_record/text2speech/qige.json', 'r+', encoding='utf-8') as fj:
        jsondata = json.load(fj)
        if input in jsondata:
            savepath = jsondata[input]
        else:
            pinyin_text = pypinyin.pinyin(input, style=pypinyin.NORMAL)
            pinyin_text = '_'.join([i[0] for i in pinyin_text])
            savepath = os.path.join('/home/robot/catkin_dt/src/voice_pkg/temp_record/text2speech', pinyin_text + '.wav')
            get_tts(input, savepath)

    global playstate
    if index == 1000:
        while True:
            if playstate == 'stop':
                playsound_work(savepath)
                time.sleep(0.15)  # 避免冲突
                return

    while True:
        if playstate == 'stop':
            thread.start_new_thread(playsound_work, (savepath,))
            time.sleep(0.15)
            break

    return 'tts is over'


if __name__ == "__main__":
    text = sys.argv[1]
    savepath = sys.argv[2]
    
    # 处理多音字等特殊情况
    # with open('/home/robot/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/duoyin.json', 'r+', encoding='utf-8') as fj:
    #     jsondata = json.load(fj)
    
    for k, v in jsondata.items():
        if k in text:
            text = text.replace(k, jsondata[k])

    # 调用 TTS 功能并播放生成的音频
    get_tts(text, savepath)
    tts_playsound(text)
