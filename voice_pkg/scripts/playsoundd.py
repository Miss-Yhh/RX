
import os
import signal
import subprocess
import time
import json
from datetime import datetime
import pypinyin

Last_Play_Processor = None
def text2speech(text='', index=0, card=0):
    '''
    使用json保存所有识别过的文件，注意音色变换之后需要重新生成。。。。
    '''
    global Last_Play_Processor

    with open('/Users/winstonwei/Documents/wmj_workspace/zt_ros/scripts/kedaxunfei/text2speech.json', 'r+', encoding='utf-8') as fj:
        jsondata = json.load(fj)
        if text in jsondata:
            print('already has')
            audio_file_savepath = jsondata[text]
        else:
            print('not file exist')
            pinyin_text = pypinyin.pinyin(text, style=pypinyin.NORMAL)
            pinyin_text = '_'.join([i[0] for i in pinyin_text])
            audio_file_savepath = os.path.join('/Users/winstonwei/Documents/wmj_workspace/zt_ros/scripts/kedaxunfei/temp_record', pinyin_text+'.wav')
            print(audio_file_savepath)

            ttsproc = subprocess.Popen(["python3", "/Users/winstonwei/Documents/wmj_workspace/zt_ros/scripts/kedaxunfei/tts_ws_python3_demo.py", text, audio_file_savepath])
            while ttsproc.poll() is None:
                time.sleep(0.1)
            jsondata[text] = audio_file_savepath
            fj.seek(0)
            json.dump(jsondata, fj, ensure_ascii=False)

    while Last_Play_Processor and Last_Play_Processor.poll() is None:
        print('last process is working, waiting')
        time.sleep(0.1)
        stop_playback(Last_Play_Processor)


    '''
    aplay播放设置参数：

    aplay -t raw -c 1 -f S16_LE -r 8000 test2.pcm

    -t: type raw表示是PCM
    -c: channel 1
    -f S16_LE: Signed 16bit-width Little-Endian
    -r: sample rate 8000

    PCM是最raw的音频数据，没有任何头信息。WAV文件就是PCM+头信息，头信息就是上述的声道数，sample rate这些。所以WAV文件可以直接播放，而PCM需要手动指定这些信息之后才能播放。
    ————————————————

                                版权声明：本文为博主原创文章，遵循 CC 4.0 BY-SA 版权协议，转载请附上原文出处链接和本声明。
                            
    原文链接：https://blog.csdn.net/qq_38350702/article/details/108336093


    alsa设置默认声卡：https://blog.csdn.net/hunanchenxingyu/article/details/48399585
    '''
    # playproc = subprocess.Popen(["aplay", "-D", f"plughw:{card},0", '-f', 'S16_LE', '-r', '16000', '-c', '1', f'{audio_file_savepath}'])
    playproc = subprocess.Popen(['python3', '/Users/winstonwei/Documents/wmj_workspace/zt_ros/scripts/kedaxunfei/playaudio.py', audio_file_savepath])
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            print('play process is working')
            return
    else:
        # 异步播放:
        Last_Play_Processor = playproc
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'

def stop_playback(process):
    '''
    信号类型：
    process.kill() 默认发送 SIGKILL 信号到进程。这是一个“硬终止”，意味着操作系统会立即终止进程，不给它任何清理或保存状态的机会。
    process.send_signal(signal.SIGTERM) 发送 SIGTERM 信号，这是一个“软终止”。它告诉进程需要终止，但允许进程执行自己的退出清理程序，如关闭文件、释放资源等。
    '''
    process.send_signal(signal.SIGTERM)
    stdout, stderr = process.communicate()
    print("Process has been stopped(terminated).")
    if stderr:
        print("Errors:", stderr.decode())



if __name__ == '__main__':
    for i in range(3):
        print(f'这是{i}个人', i)
        text2speech(f'这是{i}个人', 0, 0)