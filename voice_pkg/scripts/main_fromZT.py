# import re
# import os
# import ast
# import json
# import time
# import yaml
# import random
# import inspect
# import threading
# import subprocess
# from time import sleep
# import _thread as thread
# from datetime import datetime
# from typing import Dict, List, Tuple, Optional
# import pypinyin

# from test_host_3090_iat import iat_web_api, kedaxunfei_iat_service
# import rospy
# from std_msgs.msg import String, Bool

# from GlobalValues import GlobalValuesClass
# from interrupt.PPL.api import get_task_type, get_llm_answer
# from ./qa import stream_qa

# STATUS = GlobalValuesClass(name="Anythin is OK")
# STATUS_DICT = STATUS.get_states_dict()

# def text2speech(text='', index=0, is_beep=False, wavfile=None, ignore_interrupt=False):
#     # 如果喇叭不存在就直接跳过
#     if not STATUS.SOUND_OUTPUT_EXIST:
#         print(f"喇叭不存在: {text}")
#         sleep(1)
#         return

#     savepath = os.path.join('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech', str(time.time())+'.wav')
#     if not wavfile:
#         ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
#         while ttsproc.poll() is None:
#             if STATUS.is_Interrupted:
#                 break
            
#     while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
#         if STATUS.is_Interrupted:
#             STATUS.Last_Play_Processor.kill()
#             if not ignore_interrupt:
#                 return None
#             else:
#                 break
            
#     if STATUS.is_Interrupted:
#         if not ignore_interrupt:
#             return None
        
#     if text:  
#         if is_beep:
#             STATUS.set_LAST_BROAD_WORDS(STATUS.LAST_BROAD_WORDS + text)
#         else:
#             STATUS.set_LAST_BROAD_WORDS(text)
    
#     print(f"正在播音...({text})")
#     if wavfile:
#       savepath = wavfile
#     savepath_louder = savepath.replace('.wav', 'louder.wav')
#     cmd = f"ffmpeg -loglevel quiet -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -filter:a \"volume={STATUS.SOUND_CHANGE}dB\" -y {savepath_louder}"
#     _ = os.system(cmd)
#     playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{savepath_louder}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#     if index == 1000: 
#         while playproc.poll() is None:
#             if STATUS.is_Interrupted and not ignore_interrupt:
#                 playproc.kill()
#                 return
#         STATUS.set_Last_Play_Processor(None)
#     else:
#         STATUS.set_Last_Play_Processor(playproc)
#         time.sleep(0.15)
#     return 'tts is over'

# def listenuser(text='ding', iter=1):
#     if STATUS.SOUND_INPUT_EXIST:
#         userword = iat_web_api(text, iter=iter, environment_name='DJI_sitting_at_desk', card=STATUS.card_id)
#     else:
#         userword = input("请输入：")
#     return userword

# def pardon(pardon_round=1):#参数：迭代次数为1
#     print(f"开始录制用户语音")
#     userword = ''#存储用户的语音输入
#     repeat_count = 0  #记录用户提问的次数
#     while True:#进入无限循环，直到成功获取用户语音输入或者满足退出条件
#         userword = listenuser('ding', iter=pardon_round)
#         if userword and userword != '####':#有效输入：退出
#             break
#         elif userword == '####' or repeat_count < 1:
#         #没能成功识别用户语音，并且系统还没有重复提示过用户
#             print('大家现在可以向我提问', datetime.now())
#             text2speech("大家现在可以向我提问", index=1000, is_beep=True, wavfile='/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/canaskme.wav')
#             repeat_count += 1
#         else:#次数上限，并且未能获取有效输入
#             STATUS.set_is_QAing(False)#表示不再处于问答状态
#             while True:#进入另一个循环，直到检测到打断信号
#                 if STATUS.is_Interrupted:  
#                     STATUS.set_is_Interrupted(False)
#                     text2speech("大家现在可以向我提问", index=1000, is_beep=True, ignore_interrupt=True, wavfile='/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/canaskme.wav')
#                     break
#         STATUS.set_is_QAing(True)#设置问答状态
#         STATUS.set_is_Interrupted(False)#重置打断状态
#     return userword

# #记录语音识别的结果
# def record_speech_recognition(recognition_result):
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/SpeechRecognition.txt', 'a') as f:
#         f.write(f"时间：{current_time}\n")
#         f.write(f"上一句播音的话：{STATUS.LAST_BROAD_WORDS}\n")
#         f.write(f"语音识别结果：{recognition_result}\n\n")
        
# #记录用户输入的指令及其分类结果
# def record_task_classification(user_command, classification_result):
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/TaskClassification.txt', 'a') as f:
#         f.write(f"时间：{current_time}\n")
#         f.write(f"用户指令：{user_command}\n")
#         f.write(f"分类结果：{classification_result}\n\n")

# #Jilu问答系统的历史问题以及当前问题，回答，以及参考文档
# def record_question_answer(old_question, old_complete_answer, question, answer):
#     with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/QuestionAnswer.txt', 'a') as f:
#         f.write(f"上一轮问题：{old_question}\n")
#         f.write(f"上一轮回答：{old_complete_answer}\n")
#         f.write(f"问题：{question}\n")
#         f.write(f"回答：{answer}\n")

        
# def task_class_result_replace(result):
#     if '问答' in result:
#         return 'qa'
#     elif '休眠' in result:
#         return 'sleep'
#     elif '音量变大' in result:
#         return 'soundbig'
#     elif '音量变小' in result:
#         return 'soundsmall'
#     elif '继续' in result:
#         return 'continue'
#     else:
#         return 'bad continue'

# class InterruptClass:
#     def __init__(self, qa_class:object):
#         global STATUS
#         self.qa_class = qa_class #将传入的问答类实例复制给qa_class,用于生成用户问题的回答
#         self.pre_next_situation = False #是否在用户的文旦中出现上一个或者下一个目标点的情况

#     #监听打断信号，直接返回全局变量中是否有打断信号
#     def listen_for_INT(self) -> bool:
#         return STATUS.is_Interrupted
    
#     def handle_interrupt(self, ):
#         """处理所有情况下用户打断的操作。

#         """
#         name = self.get_self_name() # 获取调用该方法的类的名称，例如NavigationClass, ExplainClass等
#         print(f"\n处理 {name} 过程中的打断")
        
#         STATUS.set_is_QAing(True) # 防止问答被打断 - 开始
        
#         task = 'qa'
#         clear = True # 是否清楚展品名称、是否正确理解了用户的问题
#         while true:
#             # 一直进行问答，直到task不是QA，转而进行其他操作
#             while "qa" in task:
#                 sleep(0.05)
                  
#                 if clear and self.qa_class.interrupt_stream:#问答流正常
#                     #定向指定了一个提示音的路径：大家有什么问题嘛
#                     anybodyquestions = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/anybodyquestionss.wav'
#                     #另一个提示音：我在
#                     iamhere = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/iamhere.wav'
                
#                     print("In InterruptClass.handle_interrupt 接下来使用text2speech播音“大家有什么问题吗？”")
                
#                     if 'InterruptClass' in name:
#                         text2speech('有什么问题吗？', index=1000, is_beep=True, wavfile=anybodyquestions, ignore_interrupt=True) # 提示用户说出问题
#                     else:
#                         print(f"播放我在之前STATUS.is_Interrupted:{STATUS.is_Interrupted}")
#                         text2speech('我在', index=0, is_beep=True, wavfile=iamhere, ignore_interrupt=True) # 提示用户说出问题
                
#                 STATUS.set_is_Interrupted(False)#表示目前没有新的打断状态
                    
#                 self.qa_class.interrupt_stream = True#问答流可以正常进行
                
#                 question = pardon() # 录制用户的指令
#                 # print(f"\n用户指令: {question}\n")
                
#                 # 使用任务分类大模型
#                 task_result = get_task_type(text=question,model=STATUS.MODEL_TASK_TYPE)  
#                 # 任务分类，两个变量分别为用户的提问和指定用于任务分类的语言模型类型
#                 task = task_class_result_replace(task_result)#替换当前的task
#                 record_task_classification(question, task)#记录下来
#                 print('------task 任务判断结束时间=', datetime.now())
                    

#                 if task == 'qa':
#                     if clear: # 如果清楚展品名称，就直接回答
#                         STATUS.set_is_QAing(False) # 防止问答被打断 - 结束

#                         self.qa_class.answer_question(question) # 生成答案并播音
#                         STATUS.set_is_QAing(True) # 防止问答被打断 - 开始
#                     else:
#                         text2speech('大家还有其他问题吗？', index=1000, is_beep=True)

#             if 'sleep' in task:
#                 STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
            
#             elif 'soundbig' in task:
#                 # os.system('amixer -c 0 set Master 10%+')
#                 STATUS.set_SOUND_CHANGE(STATUS.SOUND_CHANGE+3)
#                 text2speech("我已经为您调大音量，您还有其他问题吗", index=1000)
#                 task = 'qa'
#                 STATUS.set_is_Interrupted(False)
#                 continue
                
#             elif 'soundsmall' in task:
#                 # os.system('amixer -c 0 set Master 10%-')
#                 STATUS.set_SOUND_CHANGE(STATUS.SOUND_CHANGE-3)
#                 text2speech("我已经为您调小音量，您还有其他问题吗", index=1000)
#                 task = 'qa'
#                 STATUS.set_is_Interrupted(False)
#                 continue
            
#             elif 'continue' in task:
#                 STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
#                 return 'continue'

#             else:
#                 pass

#         STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
    
#     def get_self_name(self):
#         return self.__class__.__name__

# class QAClass():
#     def __init__(self):
#         #初始化问答模型的线程
#         self.qaclass_thread = threading.Thread(target=self.QAClassInit,)
#         #启动问答模型的初始化
#         self.qaclass_thread.start()
#         #标志着问答流是否被打断
#         self.interrupt_stream = True

#         self.task_type_label_list = ['休眠', '继续']  # 定义可能的任务类型
#         #用于存储完整的回答
#         self.complete_answer = ""
    
#     def QAClassInit(self):#初始化语言模型类实例
#         LLMClass = get_llm_answer(model=STATUS.MODEL_LLM_ANSWER, stream_bool=STATUS.STREAM_RETURN)
#         #get_llm_answer加载大模型
#         self.llmclass = LLMClass
    
#     def answer_question(self, user_words: str) -> str:
#         #问答模型初始化
#         elf.qaclass_thread.join()
#         self.interrupt_stream = False

#         #随机选择一个过渡词然后播放
#         guodus = ['好', '好的']
#         choice = random.randint(0, len(guodus) - 1)
#         text = guodus[choice]
#         wavfile = f'/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/{text}.wav'
#         text2speech(text=text, index=0, wavfile=wavfile)

#         if STATUS.STREAM_RETURN:#使用流式返回
#             #初始化分隔符和缓存
#             splitters = [',', ';', '.', '!', '?', ':', '，', '。', '！', "'", '；', '？', '：', '/', '\n']
#             numbers = [str(c) for c in range(10)]  # 数字字符列表
#             buffer = ""
#             if_anaphora=false

#             #调用 self.llmclass.process_query() 来处理用户问题 user_words，
#             #并获取流式返回的每个 qa_answer 片段。
#             for qa_answer in self.llmclass.process_query(query=user_words, if_anaphora=if_anaphora, exhibition=STATUS.Current_Area, extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""), commentary_speech=STATUS.COMMENTARY_SPEECH):

#                 if STATUS.is_Interrupted:#如果系统被打断
#                     #记录问题和已经生成的部分回答
#                     record_question_answer(self.llmclass.old_question, self.llmclass.old_complete_answer, user_words, self.complete_answer)
#                     self.complete_answer = ""
#                     self.interrupt_stream = True
#                     break
                
#                 #累积答案到缓存
#                 if qa_answer:
#                     self.complete_answer += qa_answer
#                     buffer += qa_answer

#                     #检查最后一个字符是否是分隔符
#                     #如果是则通过TTS播放缓存中的内容
#                     if buffer[-1] in splitters:
#                         text2speech(buffer, index=0)
#                         buffer = ""

#             if not self.interrupt_stream:#如果没有被打断
#                 if buffer:#如果循环结束后，缓存里面仍然有内容，播放他
#                     text2speech(buffer, index=1000)
#                 else:#如果没有剩余内容就播放一个？
#                     text2speech("？", index=1000)
                  
#                 #记录完整的问答过程
#                 record_question_answer(self.llmclass.old_question, self.llmclass.old_complete_answer, user_words, self.complete_answer)
#                 self.complete_answer = ""
            
#         else:#非流式返回的处理
#             #直接获取完整的回答
#             qa_answer = self.llmclass.process_query(user_words, if_anaphora=if_anaphora, exhibition=STATUS.Current_Area, extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""), commentary_speech=STATUS.COMMENTARY_SPEECH)
#             record_question_answer(self.llmclass.old_question, self.llmclass.old_complete_answer, user_words, qa_answer)
#             #记录下来然后一次性播放
#             text2speech(qa_answer, index=1000)

#         if self.interrupt_stream:#如果问答被打断就等待50ms
#             sleep(0.05)
#             STATUS.set_is_Interrupted(False)
        
#         else:
#             pass
#             # text2speech('我说完了，大家还有问题吗？', index=1000, is_beep=True)
            
#         # STATUS.set_is_QAing(False)


# class MainClass:
#     def __init__(self):
#         self.settings() #调用setting方法，配置全局设置

#         #设置声卡
#         if_card_set_success = self.set_master_index_by_keyword()#尝试通过关键词设置主声卡
#         if if_card_set_success:
#             STATUS.set_card_id(-1)## 如果成功设置声卡，设置全局状态的 card_id 为 -1
#         else:
#             STATUS.set_card_id(self.get_card_index_by_keyword('ALC'))## 如果设置失败，尝试通过另一个关键词 ALC 来设置声卡。
#         print("\nSTATUS.card_id: ", STATUS.card_id)#打印设置的声卡的id

#         #这是麦克风
#         result = self.set_mic_index_by_keyword('alsa_input.usb-iflytek_XFM-DP-V0.0.18_1c00142575854862490-01.mono-fallback')
#         if result:
#             print('mic set success!')
#         else:
#             print('mic set error')

#         self.qa_class = QAClass()#实例化问答类
#         self.start = InterruptClass(self.qa_class)#实例化打断处理类

#         rospy.init_node('interrupt', anonymous=False)
#         # # 初始化 ROS 节点，节点名为 'interrupt'，anonymous=False 表示不使用匿名名称。

#         if STATUS.SOUND_INPUT_EXIST:#存在录音设备
#             ## 订阅 ivw_chatter 话题，监听唤醒词
#             # rospy.Subscriber 监听某个话题的消息，当有新消息发布的时候调用指定的回调函数
#             self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback)
#             #也就是说，每当有新消息发布时，调用ivw_callback来处理收到的消息
#             #这里的ivw_chatter可能是一个语音识别节点，监测用户的语音，监测到唤醒词时就发布一个包含唤醒信号的消息。
        
#         print("\033[33mGlobalValues---INFO---\033[0m")#打印全局信息
#         self.welcome()#调用welcome方法，执行迎宾流程

#     def get_card_index_by_keyword(self, keyword):
#         result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
#         if result.returncode != 0:
#             print("Error executing arecord -l")
#             return None
#         match = re.search(r'card (\d+):.*' + re.escape(keyword), result.stdout)
#         if match:
#             return int(match.group(1))
#         else:
#             return None

#     def set_master_index_by_keyword(self, keyword='alsa_output.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.analog-stereo'):
#         result = subprocess.run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
#         if result.returncode != 0:
#             print("Error executing arecord -l")
#             return None
#         match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
#         if match:
#             masterid = int(match.group(1))
#         else:
#             return False
#         result = subprocess.run(['pactl', 'set-default-sink', str(masterid)], capture_output=True, text=True)
#         return True

#     def set_mic_index_by_keyword(self, keyword):
#         result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
#         if result.returncode != 0:
#             print("Error executing arecord -l")
#             return None
#         match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
#         if match:
#             micid = int(match.group(1))
#         else:
#             return False
#         result = subprocess.run(['pactl', 'set-default-source', str(micid)], capture_output=True, text=True)
#         return True

#     # 处理 ivw 话题的回调函数，用于处理唤醒词的回调
#     def ivw_callback(self, data):
#         if not STATUS.is_QAing:#如果当前没有进行问答，设置状态为已经打断
#             print(f"收到打断信号！现在可以打断", datetime.now())
#             STATUS.set_is_Interrupted(True)
#         else:#如果问答，不允许打断
#             print(f"收到打断信号！现在不可以打断")

#     def settings(self):
#         STATUS.set_ROBOT_NAME('K')#机器人名称

#         STATUS.set_Enable_QA(True)#开启问答功能

#         STATUS.set_TAKE_ACTION_QA(False)#问答时是否需要机器人做动作

#         STATUS.set_SOUND_INPUT_EXIST(True)#是否存在录音设备
#         STATUS.set_SOUND_OUTPUT_EXIST(True)#播音设备

#         STATUS.set_MODEL_TASK_TYPE('qwen1_5')   # chatglm gpt-4 gpt-3.5-turbo qwen1_5
#         #设置大语言模型任务类型

#         STATUS.set_MODEL_LLM_ANSWER('huozi')#设置用于回答的任务类型

#         STATUS.set_STREAM_RETURN(True)#是否采用流式输出
#         STATUS.set_MODEL_BAN_OPENAI(False)#是否禁用openai

#         STATUS.set_DURATION(15)#无人讲话时每轮录音持续时间为15
#         STATUS.set_THRESHOLD_AUDIO(25)#录音的音量阈值，超过25代表有人讲话

#         if STATUS.MODEL_BAN_OPENAI:#如果openai被禁用，备用的模型
#             STATUS.set_MODEL_TASK_TYPE('chatglm')
#             STATUS.set_MODEL_LLM_ANSWER('chatglm')
#         STATUS.print_all_status()#打印当前所有状态
    
#     #用于迎接用户和唤醒机器人的阶段
#     def welcome(self):
#         while True:
#             print("进入welcome阶段")

#             sleep(0.05)
#             STATUS.set_is_Interrupted(False)#打断状态设置为false

#             text2speech("各位游客大家好，我是小红" , index=0)
            
#             STATUS.set_is_QAing(True)#设置问答状态为true
#             text2speech("请说 “小红小红” 来唤醒我", index=1000)
#             STATUS.set_is_QAing(False)

#             print("welcome唤醒提示音结束")

#             #语音唤醒检测的内循环
#             sound_wake_up_count = 0
#             while sound_wake_up_count < 800:
#                 if STATUS.SOUND_INPUT_EXIST:#如果录音设备存在
#                     if STATUS.is_Interrupted:#如果监测到打断信号
#                         break
#                 sleep(0.01)
#                 sound_wake_up_count += 1#增加唤醒计数

#             #这里刚刚跳出了800的循环，如果接受到打断信号，并且录音设备存在
#             if STATUS.SOUND_INPUT_EXIST:
#                 if STATUS.is_Interrupted:
#                     sleep(0.05)
#                     STATUS.set_is_Interrupted(False)
#                     break
        
#         sleep(0.05)
#         STATUS.set_is_Interrupted(False)
#         #重置打断状态，set_is_Interrupted这个是一个函数，作用是设置is_Interrupted的值
#         #系统就可以继续处理新的打断
#         self.main()

#     #所以说执行到main（）时，一定已经被唤醒    
#     def main(self):
#         if_start = self.start.handle_interrupt()
#         #通过 handle_interrupt 函数处理用户打断信号，获取是否开始参观的指令

#         #如果用户选择开始参观
#         if if_start == 'start':
#             print("开始")

#         while True:
#             # 如果开启问答功能，且讲解成功并且没有额外导航点，则进入问答环节
#             if STATUS.Enable_QA and if_success_explain and not self.find_next_destination(current_destination):
#                 print(f"\n执行问答\n")
#                 self.start.handle_interrupt()
        
#         text2speech("参观到此结束，欢迎再来哈工大找我玩。", index=1000)
#         print("任务结束")
        

# if __name__ == "__main__":
#     main_class = MainClass()
# from utils import play_sound
# from multiprocessing import Process
# path='/home/hit/RX/voice_pkg/src/kedaxunfei_ivw/testAudio/等一下2output.wav'
# play_sound(path)
# playproc = Process(target=play_sound, args=(path,))
#         # 启动新进程
# playproc.start()
import re
import os
import ast
import json
import time
import yaml
import random
import inspect
import threading
import subprocess
from time import sleep
import _thread as thread
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pypinyin
from mic_ctl import record
from utils import play_sound,get_mic_from_audio
from test_host_3090_iat import iat_web_api, kedaxunfei_iat_service
from test_host_3090_tts import get_tts
from iat import run_iat

from multiprocessing import Process
from tts import get_tts
from XF import XFSerialProtocol, XFJsonProtocol


import rospy
from std_msgs.msg import String, Bool

from GlobalValues import GlobalValuesClass
#from interrupt.PPL.api1 import get_llm_answer
from qa import intention_detect,stream_qa

record_index = -1
def text2speech(text=''):
        savepath = '/home/hit/RX/voice_pkg/scripts/kedaxunfei_tts/hao.wav '
        get_tts(text,savepath)

a=('好')
text2speech(a)

    