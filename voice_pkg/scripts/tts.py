#!/usr/bin/env python3
# ===========================================================
# 旧的 tts.py
# 新的3090本地在/home/ps/RX_hsong/RX/test_host_3090_tts.py
# 2024.5.27 hsong
#
# MODIFIED FOR ROBUSTNESS: 2025-06-21
# - Added success/failure tracking.
# - Enhanced error logging for easier debugging.
# - On TTS failure, explicitly creates a silent WAV file
#   to prevent playback of incorrect, old audio files.
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
import sys

# 全局变量来定义发音人和API凭证
# "xiaoyan","aisjiuxu","aisxping", "aisjinger","aisbabyxu"
VCN_PERSON = "x4_yezi" # 发音人
# 请将这里替换为你的有效讯飞API凭证
APPID = 'a2134d0d'
APISECRET = 'MWE2OGFhNzU4NjQyMzY2ZTE2MDI2MTA4'
APIKEY = '2d7adeb077be37f33dd9f5df67003080'


class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {
            "aue": "lame",          # LAME编码的MP3
            "sfl": 1,               # 需要流式返回
            "auf": "audio/L16;rate=16000",
            "vcn": VCN_PERSON,      # 发音人
            "tte": "utf8",
            "bgs": 0,
            "speed": 50,
            "volume": 50,
            "pitch": 50
        }
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
    # 使用一个列表来跨函数作用域跟踪成功状态
    # 列表是可变对象, 可以在回调函数中修改它
    tts_status = {'success': False, 'code': -1, 'message': 'Not started'}

    def on_message(ws, message):
        try:
            message = json.loads(message)
            if message is None:
                print('TTS WARN: Detect null frame, returning.')
                return
            
            code = message.get("code")
            sid = message.get("sid")
            
            if code != 0:
                errMsg = message.get("message", "Unknown error")
                print(f"TTS ERROR: Sid:{sid} call error: {errMsg} (code: {code})")
                tts_status['success'] = False
                tts_status['code'] = code
                tts_status['message'] = errMsg
                ws.close()
                return

            data = message.get("data")
            if data is None:
                print('TTS WARN: The message["data"] is None, returning.')
                return

            audio = data.get("audio")
            status = data.get("status")

            if audio:
                audio_decoded = base64.b64decode(audio)
                with open(save_path, 'ab') as f:
                    f.write(audio_decoded)

            if status == 2:
                print(f"TTS INFO: Successfully received all audio data for SID: {sid}")
                tts_status['success'] = True
                tts_status['code'] = 0
                tts_status['message'] = 'Success'
                ws.close()

        except Exception as e:
            print(f"TTS FATAL: Exception during message processing: {e}")
            print(f"Original message: {message}")
            tts_status['success'] = False
            tts_status['message'] = str(e)
            ws.close()

    def on_error(ws, error):
        # 这个回调在发生网络错误等底层问题时触发
        error_msg = f"TTS WebSocket Error: {error}"
        print(f"TTS FATAL: {error_msg}")
        tts_status['success'] = False
        tts_status['message'] = error_msg


    def on_close(ws, a, b):
        print("TTS INFO: WebSocket connection closed.")

    def on_open(ws):
        def run(*args):
            try:
                d = {
                    "common": wsParam.CommonArgs,
                    "business": wsParam.BusinessArgs,
                    "data": wsParam.Data}
                d_str = json.dumps(d)
                print(f"TTS INFO: Sending request for text: '{wsParam.Text[:30]}...'")
                ws.send(d_str)
                
                # 在发送请求前清除旧文件
                if os.path.exists(save_path):
                    os.remove(save_path)
            except Exception as e:
                print(f"TTS FATAL: Failed to send request on open: {e}")
                ws.close()

        thread.start_new_thread(run, ())

    wsParam = Ws_Param(APPID, APIKEY, APISECRET, text_input)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    return tts_status

def create_silent_wav(path, duration_ms=100):
    """在指定路径创建一个短小的静音WAV文件"""
    sample_rate = 16000
    num_channels = 1
    sampwidth = 2 # 16-bit
    num_frames = int(sample_rate * (duration_ms / 1000.0))
    
    try:
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(num_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(b'\0' * num_frames * num_channels * sampwidth)
        print(f"TTS FALLBACK: Created silent WAV file at {path}")
    except Exception as e:
        print(f"TTS FATAL: Could not create silent WAV file: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python tts.py <text_to_synthesize> <output_path.wav/mp3>")
        print("Example: python tts.py \"你好\" output.mp3")
        sys.exit(1)

    text = sys.argv[1]
    savepath = sys.argv[2]
    
    print("=" * 50)
    print(f"Starting TTS for text: \"{text}\"")
    print(f"Output path: {savepath}")
    print("=" * 50)
    
    status = get_tts(text, savepath)
    
    if status['success']:
        print("\nTTS process completed SUCCESSFULLY.")
        # 如果需要，可以在这里添加播放代码进行快速测试
        # os.system(f"aplay {savepath}")
        sys.exit(0)
    else:
        print(f"\n!!! TTS process FAILED. Reason: {status['message']} (Code: {status['code']}) !!!")
        # 创建一个静音文件作为失败的标志
        create_silent_wav(savepath)
        sys.exit(1)
