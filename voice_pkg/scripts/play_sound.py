#!/usr/bin/env python3
import sys
import os
from pydub import AudioSegment
from pydub.playback import play
import subprocess
from multiprocessing import Process         
import subprocess

def play_sound(wav_path: str):
    # 使用 ffplay 播放 WAV 文件
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", wav_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10  # 设置超时为 10 秒
    )
            

if __name__ == "__main__":
    # p = f"{role}_action_over.mp3"
    savepath = sys.argv[1]
    
    # 处理多音字等特殊情况
    # with open('/home/robot/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/duoyin.json', 'r+', encoding='utf-8') as fj:
    #     jsondata = json.load(fj)
    
    # for k, v in jsondata.items():
    #     if k in text:
    #         text = text.replace(k, jsondata[k])

    # 调用 TTS 功能并播放生成的音频
    play_sound(savepath)

