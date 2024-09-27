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

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

iat_finish = True

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 0, "vad_eos": 3000, "ptt": 1, "dwa": "wpgs"}


    def create_url(self):
        url = 'wss://iat-api.xfyun.cn/v2/iat'

        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"

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


def run_iat(AudioFile) -> str:

    global iat_finish

    def on_message(ws, message):
        global iat_finish
        # print(message)
        try:
            temp = json.loads(message)
            code = temp["code"]
            sid = temp["sid"]
            
            if code != 0:
                errMsg = temp["message"]
                print("sid:%s call error:%s source is:%s" % (sid, errMsg, code))
            else:
                data = temp["data"]["result"]["ws"]
                iflast = temp["data"]["result"]["ls"]
                pgs = temp["data"]["result"]["pgs"]
                
                result = ""
                for i in data:
                    for w in i["cw"]:
                        result += w["w"]
                
                if not hasattr(wsParam, 'result'):
                    wsParam.result = []
                
                print("result: ", result)
                print("wsParam.result: ", wsParam.result)
                if pgs == 'apd':
                    wsParam.result.append(result)
                elif pgs == "rpl":
                    rg = temp["data"]["result"]["rg"]
                    print("rg:", rg)
                    wsParam.result = wsParam.result[:rg[0]-1] + [result] + ["" for i in range(rg[1] - rg[0] + 1)]+ wsParam.result[rg[1]:]
                else:
                    print("The pgs of this msg is not apd or rpl")
                    print(message)
                
                if iflast:
                    wsParam.result = "".join(wsParam.result)
                    ws.close()
                    iat_finish = True
        except Exception as e:
            print("receive msg,but parse exception:", e)
            ws.close()
            return


    def on_error(ws, error):
        print("### error:", error)


    def on_close(ws, a, b):
        # print("### closed ###")
        print("语音转文字完成，用时：")


    def on_open(ws):
        global iat_finish
        def run(*args):
            global iat_finish
            iat_finish = False
            frameSize = 8000
            intervel = 0.1
            status = STATUS_FIRST_FRAME

            with open(wsParam.AudioFile, "rb") as fp:
                while True:
                    buf = fp.read(frameSize)
                    if not buf:
                        print("hello", buf)
                        status = STATUS_LAST_FRAME
                    
                    print("Read buffer length:", len(buf))
                    
                    if status == STATUS_FIRST_FRAME:
                        d = {
                            "common": wsParam.CommonArgs,
                        	"business": wsParam.BusinessArgs,
                            "data": {
                                "status": 0,
                                "format": "audio/L16;rate=16000",
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "lame"
                            }
                        }
                        d = json.dumps(d)
                        ws.send(d)
                        status = STATUS_CONTINUE_FRAME

                    elif status == STATUS_CONTINUE_FRAME:
                        d = {
                            "data": {
                                "status": 1,
                                "format": "audio/L16;rate=16000",
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "lame"
                            }
                        }
                        ws.send(json.dumps(d))

                    elif status == STATUS_LAST_FRAME:
                        d = {
                            "data": {
                                "status": 2,
                                "format": "audio/L16;rate=16000",
                                "audio": str(base64.b64encode(buf), 'utf-8'),
                                "encoding": "lame"
                            }
                        }
                        ws.send(json.dumps(d))
                        break
                        
                    # 模拟音频采样间隔
                    # Time Control
                    time.sleep(intervel)
            
            while not iat_finish:
                continue

        thread.start_new_thread(run, ())




    wsParam = Ws_Param(APPID='e5a5ef0c', 
                       APISecret='NmVjMGZjYTk5MDMwMjU4MDA5MDgzMzUz',
                       APIKey='395a787ed8634c8fcf9414b8f511e677',
                       AudioFile=AudioFile)
    websocket.enableTrace(False)  # debug mode if True
    wsUrl = wsParam.create_url()
    time1 = datetime.now()
    text = ""
    try:
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=1)
        text = wsParam.result
    except websocket.WebSocketTimeoutException as e:
        print("WebSocket Error", e)

    time2 = datetime.now()
    print(time2 - time1, "秒")

    return text

if __name__ == "__main__":
    # AudioFile = './temp_record/record_3.mp3'
    AudioFile = "./save_waves/begin_instruction.mp3"
    #AudioFile = "/home/hit/Desktop/RX/temp_record/record_1.mp3"
    text = run_iat(AudioFile=AudioFile)
    print(text)
