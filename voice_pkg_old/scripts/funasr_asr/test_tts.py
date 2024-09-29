import json
import os
import subprocess
import time
import pypinyin


def split_sentences(text):
  sentences = []
  splitters = [',', ';', '.','!','?',':', '，', '。', '！', "'", '；', '？', '：', '/'] # 遇到这些符号就拆分句子
  numbers = [str(c) for c in range(10)] # 遇到数字不拆分句子

  sentence = "" # 用于存储句子
  pre_c = '' # 用于存储上一个字符

  # 遍历文本，切分段落为句子
  for c in (text):
      if c == '【':
          if sentence and sentence != ' ':
              sentences.append(sentence)
          sentence = c
          continue
      
      sentence += c
      # 一旦碰到标点符号，就判断目前的长度
      if c in splitters and len(sentence) > 8 + 6:
          if pre_c in numbers:
              continue
          sentences.append(sentence) # 加入句子列表
          sentence = ""
  if sentence:
      sentences.append(sentence)
  return sentences

Last_Play_Processor = None
card_id = 0

def text2speech(text='', index=0):
    import re
    def filter_letters(input_string):
        # 使用列表推导式过滤出仅包含字母的字符
        filtered_string = ''.join(re.findall(r'[A-Za-z0-9]', input_string))
        return filtered_string
    pinyin_text = pypinyin.pinyin(text, style=pypinyin.NORMAL)
    pinyin_text = '_'.join([filter_letters(i[0]) for i in pinyin_text])
    savepath = os.path.join('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech', pinyin_text+'.wav')

    ttsproc = subprocess.Popen(["/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/tts_sambert.sh", text, savepath])
    # ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/tts_as_service.py", text, savepath])
    while ttsproc.poll() is None:
        time.sleep(0.1)

    # 最后再将生成好的音频文件保存起来
    global Last_Play_Processor
    global card_id
    while Last_Play_Processor and Last_Play_Processor.poll() is None:
        # print('last process is working, waiting')
        time.sleep(0.1)
    playproc = subprocess.Popen(["aplay", "-D", f"plughw:{card_id},0", '-f', 'S16_LE', '-r', '16000', '-c', '1', f'{savepath}'])

    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            # print('play process is working')
            time.sleep(0.1)
        Last_Play_Processor = None
    else:
        # 异步播放:
        Last_Play_Processor = playproc
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'

if __name__ == '__main__':
  text = '机器人技术与系统全国重点实验室源自哈工大机器人所，始建于1986年，是我国最早开展机器人技术研究的单位之一。2018年通过二次评估，获评优秀。本实验室是高校领域内唯一与机器人相关的全国重点实验室。'
  sentences = split_sentences(text)
  for sentence in sentences:
    print("###: ", sentence)
    text2speech(sentence, 0)
