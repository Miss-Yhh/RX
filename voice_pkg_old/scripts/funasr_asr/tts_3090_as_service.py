import asyncio
import json
from multiprocessing import Process
import argparse
import wave
import numpy as np
import websockets, ssl
from datetime import datetime
import sys

server_host = "192.168.31.90"
server_port = 10096
server_ssl = 1

async def send_text(text):
    message = json.dumps(
                    {
                        "text": text,
                    }
                )
    await websocket.send(message)

async def message(savepath):
    global websocket
    frames = []
    sample_rate = 16000
    is_speaking = True
    try:
        while is_speaking:
            meg = await websocket.recv()
            if isinstance(meg, str):
                meg = json.loads(meg)
                sample_rate = meg.get("audio_fs", 16000)
                is_speaking = meg.get("is_speaking", False)
            else:
                frames.append(meg)
        CHANNELS=1
        sampwidth=2
        framerate=sample_rate
        with wave.open(savepath, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)
            wf.writeframes(b''.join(frames))

    except Exception as e:
        print("Exception:", e)


async def ws_client(text, savepath):
    time1 = datetime.now()
    global websocket
    if server_ssl == 1:
        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        uri = "wss://{}:{}".format(server_host, server_port)
    else:
        uri = "ws://{}:{}".format(server_host, server_port)
        ssl_context = None
    print("connect to", uri)
    async with websockets.connect(
        uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context
    ) as websocket:
        task = asyncio.create_task(send_text(text))
        task3 = asyncio.create_task(message(savepath))  # processid+fileid
        await asyncio.gather(task, task3)
    time2 = datetime.now()
    print(time2-time1)
    exit(0)

def get_tts(text, savepath):
    asyncio.get_event_loop().run_until_complete(ws_client(text, savepath))
    asyncio.get_event_loop().run_forever()
    

if __name__ == "__main__":
    # python sambert_speech_wmj_client.py --host 192.168.31.90 
    text = sys.argv[1]
    savepath = sys.argv[2]
    # text = '我是韦明杰'
    # savepath = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_3090.wav'
    get_tts(text, savepath)
 
