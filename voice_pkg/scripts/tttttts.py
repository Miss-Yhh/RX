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

import rospy
import pypinyin

# from voice_pkg.srv import VoiceSrv, VoiceSrvResponse

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

playstate = 'stop'
savepath = '/home/robot/catkin_dt/src/voice_pkg/temp_record/play.wav'

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, textinput):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = textinput
        self.allaudio = b''

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"aue":"lame", "sfl":1, "auf":"audio/L16;rate=16000", "vcn":"xiaoyan", "bgs":0, "tte":"utf8","speed":55}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
        #使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE"”
        #self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}

    # 生成url
    def create_url(self):
        url = 'ws://192.168.31.90:26002/createRec'
        # url = 'ws://103.8.34.136:26002/createRec'
        # # 生成RFC1123格式的时间戳
        # now = datetime.now()
        # date = format_date_time(mktime(now.timetuple()))

        # # 拼接字符串
        # signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        # signature_origin += "date: " + date + "\n"
        # signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
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
        #     "host": "ws-api.xfyun.cn"
        # }
        # # 拼接鉴权参数，生成url
        # url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


def get_tts(textinput, savepath):
    def on_message(ws, message):
        try:
            # print(message)
            message = json.loads(message)
            # print(message)
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
                # print(len(wsParam.allaudio))
                iflast = result['last']
            if iflast:
                print("ws is closed")
                # Save the recorded data as a WAV file
                wf = wave.open(savepath, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(wsParam.allaudio)
                wf.close()
                ws.close()

        except Exception as e:
            print("receive msg,but parse exception:", e, datetime.now())
            ws.close()


    # 收到websocket错误的处理
    def on_error(ws, error):
        print("### error:", error, datetime.now())


    # 收到websocket关闭的处理
    def on_close(ws,a,b):
        print("### closed ###", datetime.now())


    # 收到websocket连接建立的处理
    def on_open(ws):
        def run(*args):

            # d = {"common": wsParam.CommonArgs,
            #     "business": wsParam.BusinessArgs,
            #     "data": wsParam.Data,
            #     }
            d = {
                "sessionParams":{
                    "traceId":"tur1715748522354",
                    "reset":True,
                    "id":"tur1715748522354",
                    "abilityList":[{
                        "param":"{\"volume\":20,\"native_voice_name\":\"yezi\",\"sample_rate\":\"16000\",\"audio_coding\":\"raw\",\"endFlag\":\"true\",\"pitch\":50,\"speed\":35}",
                        "abilityCode":"tts",
                        "serviceName":"tts"
                    }]
                },
                "debug":True,
                "data":str(base64.b64encode(wsParam.Text.encode("utf-8")), 'utf-8'),
                # "data":"5L2g5aW95ZGA",
                "appid":"ef014ded",
                "firstAi":"tts",
                "scene":"main_box"
            }
            d = json.dumps(d)
            ws.send(d)
            # print(wsParam.Text)
            if os.path.exists(savepath):
                os.remove(savepath)

        thread.start_new_thread(run, ())

    
    # 测试时候在此处正确填写相关信息即可运行
    with open('/home/hit/RX/voice_pkg/scripts/config_dt.json', 'r') as fj:
        config = json.load(fj)
    APPID, APISecret, APIKey = config['kedaxunfei_appid'], config['kedaxunfei_apiSecret'], config['kedaxunfei_appkey']
    wsParam = Ws_Param(APPID=APPID, APISecret=APISecret,
                       APIKey=APIKey,
                       textinput=textinput)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    # ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_interval=2, ping_timeout=1)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    # print('-------tts is over----------')


# def tts_playsound(request):
#     input = request.input
#     index = request.index
def tts_playsound(input, index=1000):
    def playsound_work(savepath):
        global playstate
        playstate = 'playing'
        play(AudioSegment.from_mp3(savepath)+10)
        playstate = 'stop'

    # print('text = ', input)
    with open('/home/robot/catkin_dt/src/voice_pkg/temp_record/text2speech/qige.json', 'r+', encoding='utf-8') as fj:
        jsondata = json.load(fj)
        if text in jsondata:
            # print('already has')
            savepath = jsondata[text]
        else:
            # print('not file exist')
            pinyin_text = pypinyin.pinyin(text, style=pypinyin.NORMAL)
            pinyin_text = '_'.join([i[0] for i in pinyin_text])
            savepath = os.path.join('/home/robot/catkin_dt/src/voice_pkg/temp_record/text2speech', pinyin_text+'.wav')
            # print(savepath)
            get_tts(savepath, input)

    global playstate
    global lastproc
    # print('playstate = ', playstate)
    # 同步播放
    if index == 1000:
        while True:
            if playstate == 'stop':
                playsound_work(savepath)
                # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
                time.sleep(0.15)
                return
    # 异步播放:
    # if lastproc:
    #     lastproc.wait()
    # lastproc = subprocess.Popen(["python3", "/home/robot/catkin_dt/src/voice_pkg/scripts/playsound.py"])
    while 1:
        if playstate == 'stop':
            thread.start_new_thread(playsound_work, (savepath,))

            # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
            time.sleep(0.15)

            break

    # 播放是否成功 需要检测喇叭
    # return VoiceSrvResponse('tts is over')
    return 'tts is over'

lastproc = None

if __name__ == "__main__":
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

