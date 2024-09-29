#!/usr/bin/env python3
# ===========================================================
# 旧的 tts.py
# 新的3090本地在/home/ps/RX_hsong/RX/test_host_3090_tts.py
# 2024.5.27 hsong
# ===========================================================

import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import os
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

import rospy
import pypinyin


STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2

# "xiaoyan","aisjiuxu","aisxping", "aisjinger","aisbabyxu"
role = "x4_lingfeizhe_zl"
role = "xiaoyan"
class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"aue":"lame", "sfl":1, "auf":"audio/L16;rate=16000", "vcn":f"{role}", "tte":"utf8","bgs":0, "speed": 50, "volume": 50, "pitch": 50}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}

    def create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }

        url = url + '?' + urlencode(v)

        return url

def get_tts(text_input, save_path):
    def on_message(ws, message):
        try:
            message =json.loads(message)
            if message is None:
                print('Detect null frame, return.')
                return
            code = message["code"]
            sid = message["sid"]
            data = message["data"]
            if data is None:
                print('The message["data"] is None, return.')
                return
            audio = message["data"]["audio"]
            audio = base64.b64decode(audio)
            status = message["data"]["status"]
            # print(message)
            if status == 2:
                ws.close()
            if code != 0:
                errMsg = message["message"]
                print("Sid:%s call error:%s code is:%s." % (sid, errMsg, code))
            else:
                # with open(save_path, 'ab') as f:
                #     print(f"Save audio to {save_path}.")
                #     f.write(audio)
                f = open(save_path, 'ab')
                print(f"Save audio to {save_path}.")
                f.write(audio)
                f.close()

        except Exception as e:
            print(message)
            print("Receive msg, but parse exception: ", e, datetime.now())
            ws.close()

    def on_error(ws, error):
        print("Text to speech error: ", error)

    def on_close(ws, a, b):
        print("Text to speech finish.")

    def on_open(ws):
        def run(*args):
            d = {
                "common": wsParam.CommonArgs,
                "business": wsParam.BusinessArgs,
                "data": wsParam.Data}
            d = json.dumps(d)
            ws.send(d)
            
            if os.path.exists(save_path):
                os.remove(save_path)

        thread.start_new_thread(run, ())

    wsParam = Ws_Param(
                # CYF:
                # APPID='e5a5ef0c', 
                # APISecret='NmVjMGZjYTk5MDMwMjU4MDA5MDgzMzUz',
                # APIKey='395a787ed8634c8fcf9414b8f511e677',
                # SH: 有效期2024-05-24
                APPID='857d8544',
                APISecret='M2FmZDc0ODkxYzViN2NhNjkzOTM1YzA4',
                APIKey='38a2455b82eb2d59a7f31083430e16b8',
                Text=text_input)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    # p = f"{role}_action_over.mp3"
    #root_dir = "./test_mp3/"

    #get_tts("请说", f"tmp_{role}_please_say.mp3")

    # get_tts("还有什么我可以帮忙的", f"{role}_finish_instruction.mp3")
    # get_tts("很抱歉，我没有听清你说什么", f"{role}_record_nothing_beep.mp3")
    # get_tts("请让我思考一下", f"{role}_begin_qa.mp3")
    # get_tts("让我为您服务", f"{role}_begin_instruction.mp3")
    # get_tts("好的，我听到了", f"{role}_record_over.mp3")
    # get_tts("我做完动作了", f"{role}_action_over.mp3")
    # get_tts("再见，期待下次和你交流", f"{role}_byebye.mp3")
    # get_tts("很抱歉，我没有理解你的意思", f"{role}_iat_nothing_beep.mp3")
    # get_tts("我说完了，还有什么问题吗", f"{role}_qa_over.mp3")
    # get_tts("你好", f"say_hello.mp3")
    # get_tts("我是哈尔滨工业大学研制的智能人形机器人助理，灵博机器人。我来自哈尔滨工业大学机电工程学院机器人技术与系统国家重点实验室。下面由我为您介绍一下哈恰会。", "temp_intro.mp3")
    # get_tts("欢迎来到哈洽会，我是灵博机器人，我来自哈尔滨工业大学机器人技术与系统全国重点实验室，很高兴为您服务。", "introduce.mp3")
    #print("Done.Saved in ",p)
    text = sys.argv[1]
    savepath = sys.argv[2]
    
    # 处理多音字等特殊情况
    # with open('/home/robot/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/duoyin.json', 'r+', encoding='utf-8') as fj:
    #     jsondata = json.load(fj)
    
    # for k, v in jsondata.items():
    #     if k in text:
    #         text = text.replace(k, jsondata[k])

    # 调用 TTS 功能并播放生成的音频
    get_tts(text, savepath)

