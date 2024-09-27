# -*- coding: utf-8 -*-
from GlobalValues import GV
gv = GV()
if gv.SERVER_TYPE == '3090':
    from test_host_3090_iat import iat_web_api, kedaxunfei_iat_service
    from test_host_3090_tts import get_tts
else:
    from iat import run_iat
    from tts import get_tts


from qa import intention_detect, stream_qa, intention_to_instruction
from mic_ctl import record
import os
import time
import _thread as thread
import queue
from pydub import AudioSegment
from utils import play_sound, get_audio_length
from XF import XFSerialProtocol, XFJsonProtocol
import json
# from detect_action import extract_our_action_from_text

REALLY_DO = False
record_start_beep = True
record_nothing_beep = True
accumulate_sleep_time = 0
play_index = 0
record_index = 0
splitters = '[,;.!?:，。！；？：]'
play_finish = False
is_wake = False
wake_info_dict = None

def get_iat_server(
    wav_path:str,
    server_type:str=gv.SERVER_TYPE
):
    if server_type == '3090':
        # query = iat_web_api(f"./temp_record/record_{record_index}.mp3")
        query = kedaxunfei_iat_service(f"./temp_record/record_{record_index}.mp3")
    else:
        query = run_iat(f"./temp_record/record_{record_index}.mp3")
    return query


def playing(queue:queue.Queue):
    TimeWait = 10 # s
    global play_finish
    play_finish = False
    while True:
        try:
            file_path = queue.get(timeout=TimeWait)  # 10秒超时
        except:
            print(f"\033[32m{TimeWait}s 内queue仍为空\033[0m ")
            continue  

        if file_path is None:  # 检查停止信号
            play_finish = True
            return
        
        play_sound(file_path)

def run_wake_thread():
    global is_wake
    xf = XFSerialProtocol()
    xfj = XFJsonProtocol()
    while True:
        if is_wake:
            # 如果是唤醒状态，不需要再次唤醒
            time.sleep(0.1)
            continue

        msg_id, msg = xf.process()
        
        print("\033[0;37;44mGet wake up signal.\033[0m")
        is_wake = True

        msg_json_str = xfj.processJson(msg)
        wake_info_dict = json.loads(msg_json_str["content"]["info"])["ivw"]
        # {'start_ms': 1323880, 'end_ms': 1324900, 'beam': 5, 'physical': 5, 'score': 1111.0, 'power': 3273681.5, 'angle': 270.0, 'keyword': 'ni3 hao3 ling2 bo2'}

thread.start_new_thread(run_wake_thread, ())

print("Initialization finished.")

while True:
    # 休眠时间
    if not is_wake:
        continue
    
    record_index += 1
    if_record_voice = record(record_start_beep, f"./temp_record/record_{record_index}.mp3", record_nothing_beep)

    while not if_record_voice:
        record_start_beep = False
        if_record_voice = record(record_start_beep, f"./temp_record/record_{record_index}.mp3", record_nothing_beep)
        

    thread.start_new_thread(play_sound, ("./save_waves/record_over.mp3",))
    time.sleep(0.8)

    query = get_iat_server(f"./temp_record/record_{record_index}.mp3", gv.SERVER_TYPE)

    print(f"\033[33m识别结果: {query}\033[0m")

    # 判断是否识别到内容
    if query.strip() == "":
        play_sound("./save_waves/iat_nothing_beep.mp3")  # 很抱歉，我没有理解您的意思
        time.sleep(0.5)
        continue
    
    # 根据关键词执行特定逻辑
    if '再见' in query or '拜拜' in query:
        is_wake = False
        record_start_beep = True
        wake_info_dict = None
        time.sleep(0.8)
        thread.start_new_thread(play_sound, ("./save_waves/byebye.mp3",))  #再见，期待下次和您交流
        time.sleep(1.5)
        continue
    elif '系统关机' in query:
        exit(0)

    # id = extract_our_action_from_text(query)
    # print(f"\033[32m识别id为{id}\033[0m")
    # if id != -1:
    #     # TODO 识别到的动作id发送给他们

    #     if REALLY_DO:
    #         pass
    #     print("发送指令给他们")
    #     block = input("动作是否执行完成:\n")
    #     time.sleep(0.5)
    #     play_sound(f"./save_waves/action_over.mp3")

    #     record_start_beep = False
    #     continue

    # 需要识别意图的
    intention = intention_detect(query)
    
    if "动作" in intention:
        b = "./save_waves/begin_instruction.mp3"
        thread.start_new_thread(play_sound,(b,))  # 让我为您服务
        t = get_audio_length(b)

        answer = intention_to_instruction(query)  

        
        # TODO:发指令给他们
        if not REALLY_DO:
            cnt = 20
            while cnt>0:
                print(f"模拟执行动作过程ing......{cnt}")
                cnt -= 1
                time.sleep(0.1)

        
        
        time.sleep(t-0.2)
        play_sound(f"./save_waves/finish_instruction.mp3")

        record_start_beep = False

    else: # 对话意图和未识别成功都对话
        audio_path_queue = queue.Queue()

        #thread.start_new_thread(play_sound, ("./save_waves/begin_qa.mp3",))  # 我思考一下
        #time.sleep(0.7)
        # TODO TTS放在一个单独的线程里面，说话的时候完成.后台play_sound
        answer = stream_qa(query)

        print("here")
        thread.start_new_thread(playing,(audio_path_queue,))

        sen = ""
        play_index = 0
        for char in answer:
            print(char)
            
            for c in char:
                if c in [' ', '\t']: continue
                sen += c
                if c in splitters and len(sen) > 8:
                    print(sen)
                    # thread播放队列中的路径，为空或超时则结束
                    generated_path = f"/home/hit/RX/temp_record/play_{play_index}.mp3"
                    get_tts(sen, generated_path)
                    audio_path_queue.put(generated_path)
                    
                    # play_sound(f"play ./temp_record/play_{play_index}.mp3")
                    
                    time.sleep(0.05)
                    play_index += 1

                    sen = ""

        if sen != "":  # 最后一句
            print(sen)
            generated_path = f"./temp_record/play_{play_index}.mp3"
            get_tts(sen, generated_path)
            audio_path_queue.put(generated_path)
            time.sleep(0.1)
            play_index += 1  
        
        audio_path_queue.put('./save_waves/qa_over.mp3')  # 我说完了
        audio_path_queue.put(None)
        record_start_beep = False
        time.sleep(0.5)
        while not play_finish:
            time.sleep(0.05)



