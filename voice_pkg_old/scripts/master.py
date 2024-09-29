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

# from kedaxunfei_iat.iat_as_service_iter import iat_web_api
# from kedaxunfei_iat.iat_as_service import iat_web_api
from kedaxunfei_iat.test_host_3090_iat import iat_web_api
# from funasr_asr.asr_3090_as_service import iat_web_api
# from tencentclound.tencentclound import iat_tencent as iat_web_api

import rospy
from std_msgs.msg import String, Bool
try:
    from harbin_pkg.srv import moveToTarget   # 下位机移动服务
    from harbin_pkg.srv import doAction       # 下位机动作服务
    from harbin_pkg.msg import stopProcessing # 下位机暂停话题
except:
    pass
    # print("failed to import ..")
from interrupt import get_task_type
from interrupt import get_llm_answer
from GlobalValues import GlobalValuesClass
import pypinyin
# from Only_text_prompt.Robot_prompt_text import ask  #lhkong动作分类

STATUS = GlobalValuesClass(name="Anythin is OK")
STATUS_DICT = STATUS.get_states_dict()

# print(STATUS.is_Explaining)
# print(STATUS_DICT)

def text2speech(text='', index=0):
    # 如果喇叭不存在就直接跳过
    if not STATUS.SOUND_OUTPUT_EXIST:
        print(f"喇叭不存在: {text}")
        sleep(1)
        return

    savepath = os.path.join('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech', str(time.time())+'.wav')

    ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
    while ttsproc.poll() is None:
        # print('tts process is working, interrupted:', STATUS.is_Interrupted)
        if STATUS.is_Interrupted:
            print("kill tts")
            ttsproc.kill()
            return
        # time.sleep(0.1)

    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        # print('last process is working, waiting')
        if STATUS.is_Interrupted:
            print("kill last play")
            STATUS.Last_Play_Processor.kill()
            return
        # time.sleep(0.1)
    playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{savepath}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # playproc = subprocess.Popen(["aplay", "-D", f"plughw:{0},0", f'{savepath}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            # print('play process is working')
            if STATUS.is_Interrupted:
                print('kill play process')
                playproc.kill()
                return
            # time.sleep(0.1)
        STATUS.set_Last_Play_Processor(None)
    else:
        # 异步播放:
        STATUS.set_Last_Play_Processor(playproc)
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'


def text2speech_for3090(text='', index=0):
    # 如果喇叭不存在就直接跳过
    if not STATUS.SOUND_OUTPUT_EXIST:
        print(f"喇叭不存在: {text}")
        sleep(1)
        return

    import re
    def filter_letters(input_string):
        # 使用列表推导式过滤出仅包含字母的字符
        filtered_string = ''.join(re.findall(r'[A-Za-z0-9]', input_string))
        return filtered_string
    with open('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech/yezi.json', 'r+', encoding='utf-8') as fj:
        jsondata = json.load(fj)

        # 先判断是否存在了json中，如果没有就去tts生成
        savepath_pcm = None
        if text in jsondata:
            # print('already has ', text)
            savepath_pcm = jsondata[text]
            if not os.path.exists(savepath_pcm):
                savepath_pcm = None
        if not savepath_pcm:
            # print('not file exist ', text)
            pinyin_text = pypinyin.pinyin(text, style=pypinyin.NORMAL)
            pinyin_text = '_'.join([filter_letters(i[0]) for i in pinyin_text])
            savepath = os.path.join('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech', pinyin_text+'.mp3')

            # ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/tts_as_service.py", text, savepath])
            # ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/tts_3090_as_service.py", text, savepath])
            ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
            while ttsproc.poll() is None:
                # print('tts process is working, interrupted:', STATUS.is_Interrupted)
                if STATUS.is_Interrupted:
                    print("kill tts")
                    ttsproc.kill()
                    return
                # time.sleep(0.1)

            # # 模拟tts
            # cmd = f"cp /home/kuavo/catkin_dt/src/voice_pkg/temp_record/play.wav {savepath}"
            # exit_status = os.system(cmd)

            # 转为raw的格式
            savepath_pcm = savepath.replace(".mp3", "_pcm.wav")
            cmd = f"ffmpeg -loglevel quiet -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -filter:a \"volume=15dB\" -y {savepath_pcm}"
            exit_status = os.system(cmd)

            # 最后再将生成好的音频文件保存起来
            jsondata[text] = savepath_pcm
            fj.seek(0)
            json.dump(jsondata, fj, ensure_ascii=False)

    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        # print('last process is working, waiting')
        if STATUS.is_Interrupted:
            print("kill last play")
            STATUS.Last_Play_Processor.kill()
            return
        # time.sleep(0.1)
    playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{savepath_pcm}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", '-f', 'S16_LE', '-r', '16000', '-c', '1', f'{savepath_pcm}>/dev/null' , '2>&1'])

    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            # print('play process is working')
            if STATUS.is_Interrupted:
                print('kill play process')
                playproc.kill()
                return
            # time.sleep(0.1)
        STATUS.set_Last_Play_Processor(None)
    else:
        # 异步播放:
        STATUS.set_Last_Play_Processor(playproc)
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'

def text2speech_old(text='', index=0):
    '''
    需要成员变量：
    interrupt:记录是否打断
    Last_Play_Processor:记录上一个 播放音频的 process
    '''
    audio_file_savepath = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/play.wav'
    # ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/tts_as_service.py", text, audio_file_savepath])
    # while ttsproc.poll() is None:
    #     print('tts process is working, interrupted:', STATUS.is_Interrupted)
    #     if STATUS.is_Interrupted:
    #         print("kill tts")
    #         ttsproc.kill()
    #         return
    #     time.sleep(0.5)
    time.sleep(1)  # 模拟tts生成的时间
    
    newpath = audio_file_savepath.replace(".wav", "new.wav")
    
    cmd = f"ffmpeg -loglevel quiet -i {audio_file_savepath} -acodec pcm_s16le -ac 1 -ar 16000 -y {newpath}"
    exit_status = os.system(cmd)
    # playproc = subprocess.Popen([cmd])
    # playproc.wait()

    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        # print('last process is working, waiting')
        if STATUS.is_Interrupted:
            print("kill last play")
            STATUS.Last_Play_Processor.kill()
            return
        time.sleep(0.5)

    playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{newpath}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # playproc = subprocess.Popen(['python3', '/Users/winstonwei/Documents/wmj_workspace/zt_ros/scripts/kedaxunfei/playaudio.py', audio_file_savepath])

    
    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            print('play process is working')
            if STATUS.is_Interrupted:
                print('kill play process')
                playproc.kill()
                return
            time.sleep(0.5)
        STATUS.set_Last_Play_Processor(None)
    else:
        # 异步播放:
        STATUS.set_Last_Play_Processor(playproc)
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'

def listenuser(text='ding', iter=1):
    # 可选的录音保存路径：
    # % DJI_sitting_at_desk         % 坐在办公桌前，手持小蜜蜂
    # % DJI_stand_next_robot        % 站在机器人旁边（1-2米），手持小蜜蜂
    # % DJI_very_close_robot        % 小蜜蜂放在距离机器人风扇非常近的地方，比如放在机器人肩膀上
    # % HEAD_stand_next_robot       % 站在机器人旁边（1-2米），使用头部麦克风
    # % HEAD_very_close_robot       % 说话时非常贴近头部麦克风
    # 特殊情况添加以下后缀：
    # % _noisePeople                % 环境中有很多人声，非常吵
    # % _quiet                      % 周围基本没什么人说话，很安静

    if STATUS.SOUND_INPUT_EXIST:
        userword = iat_web_api(text, iter=iter, environment_name='DJI_sitting_at_desk', card=STATUS.card_id)
    else:
        userword = input("请输入：")

    return userword

def pardon(pardon_round=1):  # TODO:utils.
    # 反复录制用户语音，直至语音不为空，最多重复pardon_round轮
    print(f"开始录制用户语音")
    
    userword = ''
    
    # userword = listenuser('ding', iter=pardon_round)
    while True:
        userword = listenuser('ding', iter=pardon_round)
        
        if userword:
            break
        else:
            text2speech("大家现在可以向我提问", index=1000)  # 用户超过 6 秒没有说话就询问一遍

    # print(f"录制结束，录制结果为: {userword}")
    text2speech("好的", index=0)
    # userword = input()
    return userword


class InterruptClass:
    def __init__(self, qa_class:object):
        global STATUS
        
        self.qa_class = qa_class # 传入的问答类实例用于生成用户问题的回答

    def listen_for_INT(self, ) -> bool:
        """监听打断信号, 返回是否打断
        
        """
        return STATUS.is_Interrupted
        
    def handle_interrupt(self, ):
        """处理所有情况下用户打断的操作。

        """
        name = self.get_self_name() # 获取调用该方法的类的名称，例如NavigationClass, ExplainClass等
        # print(f"\n处理 {name} 过程中的打断")
        
        STATUS.set_is_QAing(True) # 防止问答被打断 - 开始
        STATUS.set_is_Interrupted(False)  # 由于已经在处理打断，故消除打断flag

        # TODO: 机器人如何转向面朝用户？用户人脸居中才停下来，如果有多个人脸就匹配最大的

        if STATUS.FACE_DETECT and STATUS.LOW_COMPUTER_EXIST:
            print("STATUS.is_Big_Face_Detected: ", STATUS.is_Big_Face_Detected)
            while not STATUS.is_Big_Face_Detected: # 视野中没有人脸
                # TODO: 向下位机发送转向命令
                # TODO: 如何判断向左还是向右？

                print("\n向下位机发送转向命令")
                rospy.wait_for_service('TurningService') # 等待与下位机通信的服务变得可用
                try:
                    turn = rospy.ServiceProxy('add_two_ints', AddTwoInts) # 创建服务代理，用于调用服务
                    responce = turn(int(2)) # 向服务发送请求，阻塞，直至到达目标点才会返回，正数左传，负数右转，最大15度
                except rospy.ServiceException as e:
                    print("向下位机发送 转向 命令 - 服务报错: %s"%e)
            
            if STATUS.LOW_COMPUTER_EXIST:
                # 向下位机发送停止信号
                STATUS.Stop_Publisher.publish('stop')
            print("\n因为转向看到人脸，向下位机发送停止信号")
            STATUS.set_is_Big_Face_Detected(False)

        text2speech('大家有什么问题吗？', index=1000) # 提示用户说出问题
        task_macthed = False

        pn_flag = True
        while pn_flag: # 该循环（称为PN）的唯一作用是：如果不存在'下一个'或'上一个'展厅，机器人会提示用户重新下达指令，此时程序会跳转到该循环的开始处
            pn_flag = False

            question = pardon() # 录制用户的指令
            # print(f"\n用户指令: {question}\n")

            # text2speech('好的，我听到了。', index=0) # 缓解 任务分类 空白
            
            # 启动线程用于识别用户希望机器人执行的动作
            if STATUS.TAKE_ACTION_QA:
                self.ask_for_action_thread = threading.Thread(target=self.ask_for_action, args=(question,)) # 初始化线程
                self.ask_for_action.start() # 启动线程
            
            task_type_keywords = ['参观', '带我去', '没有问题', '没有什么问题', '继续']
            # task_type_keywords = []  # 由于想测试 把任务分类和问答 放在问答大模型中一次性完成，所以任务分类关键词列表为空，直接进入问答大模型

            if any(keyword in question for keyword in task_type_keywords):
                task_macthed = True
                task = get_task_type(question, model=STATUS.MODEL_TASK_TYPE) # 任务分类
                # print(f"\n大模型进行任务分类: ", task)
            else:
                # print(f"\n无需进行大模型任务分类，直接进入问答")
                task ='qa'

            if STATUS.TAKE_ACTION_QA:
                # 等待识别动作的大模型返回结果
                self.ask_for_action_thread.join()
                    
                if '没有动作' in STATUS.Action_from_User:
                    pass # 保持原来的任务分类
                else:
                    task = 'qa' # 做完动作进入问答任务

            # 一直进行问答，直到task不是QA，转而进行其他操作
            while "qa" in task:
                clear = True # 是否清楚展品名称

                if STATUS.POSE_DETECT: 
                    if not 'explicit' in task: # 如果问题中没有显示指出展品名称
                        # 使用空格进行分割
                        pose_detect_keywords = STATUS.POSE_DETECT_KEYWORD.split(' ')
                        
                        if len(pose_detect_keywords) > 1: # 如果有多个关键词，说明不能精准分辨
                            question_part = ', '.join(pose_detect_keywords[:-1])
                            text2speech(f"请问您指的是{question_part}, 还是{pose_detect_keywords[-1]}？", index=1000)
                            object_answer = pardon()

                            # 从用户的回答中找到关键词
                            result_object = ''
                            for keyword in pose_detect_keywords:
                                if keyword in object_answer:
                                    result_object = keyword
                                    break
                            if result_object:
                                question += "（" +  result_object + "）"
                            else:
                                clear = False
                                text2speech("对不起，我没有识别到您想让我介绍的展品", index=1000)

                        else: # 如果只有一个关键词，说明可以精准分辨
                            question += "（" +  pose_detect_keywords[0] + "）"

                        # TODO: 如果成功识别到展品名称，机器人转向展品
                        if clear: # 在问题中没有显示指出展品名称的情况下，清楚展品名称，说明成功识别到展品名称
                            pass

                if clear: # 如果清楚展品名称，就直接回答
                    STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
                    qa_model_result = self.qa_class.answer_question(question) # 生成答案并播音

                    # 如果已经通过关键词匹配到任务类型，就直接跳过问答模型的任务分类
                    if task_macthed:
                        qa_model_result = None

                    # print("问答模型进行任务分类和问答的返回值: ", qa_model_result)
                    task = qa_model_result if qa_model_result else task

                    STATUS.set_is_QAing(True) # 防止问答被打断 - 开始
                else:
                    text2speech('大家还有其他问题吗？', index=1000)

                # 如果问答模型没有返回，说明是问答任务，就进入if，执行问答任务应该执行的一系列操作
                # 否则就跳过这个if，直接执行其他任务所对应的操作（即该if后面的操作）
                if not qa_model_result:
                    question = pardon() # 录制用户的指令
                    # print(f"\n用户指令: {question}")
                
                    # 启动线程用于识别用户希望机器人执行的动作
                    if STATUS.TAKE_ACTION_QA:
                        self.ask_for_action_thread = threading.Thread(target=self.ask_for_action, args=(question,)) # 初始化线程
                        self.ask_for_action.start() # 启动线程

                    if any(keyword in question for keyword in task_type_keywords):
                        task_macthed = True
                        task = get_task_type(question, model=STATUS.MODEL_TASK_TYPE) # 任务分类
                        # print(f"\n大模型进行任务分类: ", task)
                    else:
                        # print(f"\n无需进行大模型任务分类，直接进入问答")
                        task ='qa'
                    
                    if STATUS.TAKE_ACTION_QA:
                        # 等待识别动作的大模型返回结果
                        self.ask_for_action_thread.join()

                        if '没有动作' in STATUS.Action_from_User:
                            pass # 保持原来的任务分类
                        else:
                            task = 'qa' # 做完动作进入问答任务
            
            # 在讲解过程中被打断，并且不准备继续之前的讲解，就可以清除相关变量
            if 'ExplainClass' in name and 'continue' not in task:
                self.sentences = [] # 清空句子列表
                self.index_of_sentence = 0 # 重置句子索引

            if 'visit' in task:
                # 从字符串中提取目标点（如'卫星展厅'、'下一个'）
                Index_of_Vist_Ting = [item.replace("展区", "展厅") for item in STATUS.Index_of_Vist]
                keywords = STATUS.Index_of_Vist + Index_of_Vist_Ting + ['上一个', '下一个']

                # Check if the string contains any of the elements in the list
                target_point = next((element for element in keywords if element in task or task.split(' ')[1] in element), None)

                # TODO: 思考不同任务过程中的新导航指令是否需要不同的处理（可能与更改目标点列表策略有关）

                if target_point:
                    if '下一个' in target_point: # 去往下一个展厅

                        if 'NavigationClass' in name: # 如果是导航中被打断
                            now_destination = STATUS.Current_Order_of_Visit[0]

                            if len(STATUS.Current_Order_of_Visit) > 1: # 下一个展厅是目标点列表中的第二个展厅
                                # text2speech(f"那我们跳过{now_destination}，前往下一个展厅，{STATUS.Current_Order_of_Visit[1]}", index=0)
                                STATUS.set_Destination_Area(new_Destination_Area=STATUS.Current_Order_of_Visit[1])

                            else: # 如果已经没有下一个展厅
                                text2speech(f"不好意思，{now_destination}已经是最后一个展厅，请您告诉我，想去哪个展厅还是继续去{now_destination}", index=1000)
                                pn_flag = True
                                continue
                        
                        else: # 如果并非导航过程中被打断，说明上一次导航已经结束

                            if len(STATUS.Current_Order_of_Visit) > 0: # 下一个展厅是目标点列表中的第一个展厅
                                # text2speech(f"前往下一个展厅，{STATUS.Current_Order_of_Visit[0]}", index=0)
                                STATUS.set_Destination_Area(new_Destination_Area=STATUS.Current_Order_of_Visit[0])
                            
                            else: # 如果已经没有下一个展厅
                                text2speech("不好意思，已经没有下一个展厅，请您向我提问或告诉我您要去哪个展厅", index=1000)
                                pn_flag = True
                                continue
                    
                    elif '上一个' in target_point:  # 去往上一个展厅

                        if STATUS.Last_Area != None: # 如果有上一个展厅的话
                            # text2speech(f"那我们回到上一个展厅，{STATUS.Last_Area}", index=0)
                            STATUS.set_Destination_Area(new_Destination_Area=STATUS.Last_Area)

                        else: # 如果没有上一个展厅
                            text2speech("不好意思，我们已经在第一个展厅，请您向我提问或告诉我您要去哪个展厅", index=1000)
                            pn_flag = True
                            continue
                        
                    else: # 不是'下一个'或'上一个'，而是直接给出目标点名称
                        STATUS.set_Destination_Area(new_Destination_Area=target_point)

            elif 'sleep' in task:
                pass
            
            elif 'continue' in task:
                STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
                return 'continue'

            else:
                pass

        # 如果有明确的visit指令，或者导航过程被打断后的continue指令，那就打印将要去的目标点
        if 'visit' in task or ('NavigationClass' in name and 'continue' in task):
            print("\n即将去往: ", STATUS.Destination_Area)
            print("\n目前的目标点列表: ", STATUS.Current_Order_of_Visit)

        STATUS.set_is_QAing(False) # 防止问答被打断 - 结束

    # def ask_for_action(self, question):
    #     print("\n开始识别用户希望机器人执行的动作")
    #     STATUS.set_Action_from_User(ask(question))
    #     if not STATUS.Action_from_User == '没有动作':
    #         self.send_action(STATUS.Action_from_User)
    #     else:
    #         print("\n用户不希望机器人执行动作")

    # def send_action(delf, action_name):
    #     # TODO: 向下位机发送动作指令
    #     if STATUS.LOW_COMPUTER_EXIST:
    #         try:
    #             arm_service = rospy.wait_for_service("/doAction") # 等待与下位机通信的服务变得可用
    #             command_client = rospy.ServiceProxy("/doAction", doAction) # 创建服务代理，用于调用服务
    #             response = command_client(action_code=action_name) # 向服务发送请求，阻塞，直至到达目标点才会返回
    #         except rospy.ROSException as e: # 如果通信异常
    #             print("向下位机发送 动作 命令 - 服务报错: %s"%e)

    #         print("taking action's response: ", response)
    #     else:
    #         print(f"\n向下位机发送 {action_name} 动作指令")
    
    def get_self_name(self, ):
        return self.__class__.__name__


class QAClass():
    def __init__(self):
        self.qaclass_thread = threading.Thread(target=self.QAClassInit) # 初始化问答模型的线程
        self.qaclass_thread.start()  # 启动问答模型的初始化
        self.qaclass_thread.join()
        
        self.end_stream = False  # 标志着流式返回的问答 被打断，而不是正常退出
        self.task_is_qa = True  # 标志着任务分类得到的结果是问答，而不是参观、继续、休眠之一
        self.task_type_label_list = ['参观', '休眠', '继续']
    
    def QAClassInit(self):
        LLMClass = get_llm_answer(model=STATUS.MODEL_LLM_ANSWER, stream_bool=STATUS.STREAM_RETURN)
        self.llmclass = LLMClass
    
    def answer_question(self, user_words:str) -> str:
        # STATUS.set_is_QAing(True)

        # text2speech("请稍等，让我思索一下。", index=0)
        
        # 文档检索问答模型初始化完成
        self.qaclass_thread.join()
        self.end_stream = False
        
        if STATUS.STREAM_RETURN:
            splitters = ['、', ',', ';', '.', '!', '?', ':', '，', '。', '！', "'", '；', '？', '：', '/']
            numbers = [str(c) for c in range(10)]
            buffer = ""  # 初始化缓存字符串
            for qa_answer in self.llmclass.process_query(user_words):
                if STATUS.is_Interrupted:  # 受到打断直接退出此次问答
                    self.end_stream = True
                    break
                
                if qa_answer:
                    qa_answer = qa_answer.replace('A', '诶') if 'A' == qa_answer else qa_answer
                    buffer += qa_answer  # 将流式返回的结果累加到缓存中

                    if len(buffer) == 2:
                        if buffer in self.task_type_label_list:
                            self.task_is_qa = False

                    # 检查最后一个字符是否是分隔符，并且缓存长度大于5
                    if buffer[-1] in splitters and len(buffer) > 8:
                        if len(buffer) > 1 and buffer[-2] in numbers:
                            continue  # 如果分隔符前是数字，继续累积缓存
                        
                        if self.task_is_qa:
                            # print("将大模型回答发送到喇叭:", buffer)
                            text2speech(buffer, index=0)  # 播放缓存中的内容
                        else:  # 如果任务不是问答的话，buffer永远不用清空
                            continue

                        # 由于使用了qwen，就不用拦截了
                        # if '根据' not in buffer and '参考' not in buffer:
                        #     print("将大模型回答发送到喇叭:", buffer)
                        #     text2speech(buffer, index=0)  # 播放缓存中的内容
                        # else:
                        #     print("拦截类似 根据参考文本 的句子:", buffer)
                            
                        buffer = ""  # 清空缓存
                else:
                    # print("生成器生成 None 字符")
                    pass

            if buffer:  # 如果循环结束后缓存中还有内容，也播放它
                if self.task_is_qa:
                    # print("将大模型回答发送到喇叭:", buffer)
                    text2speech(buffer, index=1000)
                else:
                    post_process_result = self.llmclass.task_class_post_process(query=buffer)

                    self.task_is_qa = True

                    if '问答' in post_process_result:
                        if '明确' in post_process_result:
                            return 'qa explicit'
                        else:
                            return 'qa'
                    elif '休眠' in post_process_result:
                        return 'sleep'
                    elif '参观' in post_process_result:
                        post_process_result = post_process_result.replace("参观", "visit")
                        return post_process_result
                    elif '继续' in post_process_result:
                        return 'continue'
        else:
            qa_answer = self.llmclass.process_query(user_words) # 问答模型处理用户问题

            if len(qa_answer) == 2:
                if qa_answer in self.task_type_label_list:
                    self.task_is_qa = False

            if self.task_is_qa:
                print("将大模型回答发送到喇叭:", qa_answer)
                text2speech(qa_answer, index=1000) # 语音回答用户问题
            else:
                post_process_result = self.llmclass.task_class_post_process(query=qa_answer)

                self.task_is_qa = True

                if '问答' in post_process_result:
                    if '明确' in post_process_result:
                        return 'qa explicit'
                    else:
                        return 'qa'
                elif '休眠' in post_process_result:
                    return 'sleep'
                elif '参观' in post_process_result:
                    post_process_result = post_process_result.replace("参观", "visit")
                    return post_process_result
                elif '继续' in post_process_result:
                    return 'continue'
        
        if self.end_stream:
            STATUS.set_is_Interrupted(False)
            sleep(0.15)
            text2speech('大家有什么问题吗？', index=1000)
        else:
            text2speech('我说完了，大家还有问题吗？', index=1000)
            
        # STATUS.set_is_QAing(False)

class NavigationClass(InterruptClass):
    def __init__(self, qa_class:object):
        super().__init__(qa_class) # 调用父类的初始化方法

        global STATUS
        
    def send_destination_and_handle_interrupt(self, destination: int):
        """通过导航目标点话题发送目标点代号 并处理打断。

        Args:
            destination_code (int): 目标点的代号。
        """
        STATUS.set_is_Navigating(True)
        STATUS.set_is_Depth_Obstacle(False)
        STATUS.set_is_Yolo_Obstacle(False)
        
        STATUS.NAVI_START_FLAG = None
        STATUS.NAVI_END_FLAG = None
            
        if STATUS.LOW_COMPUTER_EXIST:
            print(f"发送去往 {destination} 号目标点的信号\n")
            STATUS.Navi_target_Publisher.publish(str(destination))  # 通过导航目标点话题发送目标点代号
            
            wait_for_naiv_start = 0
            while True:
                if wait_for_naiv_start > 1000:
                    print("导航启动话题没有响应！")
                    STATUS.set_is_Navigating(False)
                    return False
                
                if STATUS.NAVI_START_FLAG == 'active':  # 导航顺利启动
                    print("导航顺利启动!")
                    break
                elif STATUS.NAVI_START_FLAG == 'busy':  # 导航启动失败
                    print("导航启动失败！mova base不可用！")
                    STATUS.set_is_Navigating(False)
                    return False
                
                wait_for_naiv_start += 1
                sleep(0.1)
            
            while True:
                interrupt_flag = self.listen_for_INT() # 监听打断信号
                
                # 打断后做出的处理
                if interrupt_flag:
                    if STATUS.LOW_COMPUTER_EXIST:
                        # 向下位机发送停止信号
                        STATUS.Stop_Publisher.publish('stop')
                    print("\n因为语音打断，向下位机发送停止信号")
                    
                    sleep(0.1)  # 防止 self.handle_interrupt() 太快，在 text2speech 之前把 STATUS.is_interrupted 置为 False
                    if_continue = self.handle_interrupt()  # 调用父类InterruptClass中的方法处理打断
                    if not if_continue: # 不是继续就直接结束导航
                        STATUS.set_is_Navigating(False)
                        return False
                    else: # 是继续就继续导航
                        return False
                    
                # 如果成功到达指定地点
                # print("STATUS.NAVI_END_FLAG:", STATUS.NAVI_END_FLAG)
                if STATUS.NAVI_END_FLAG == 'success':
                    STATUS.set_is_Navigating(False)
                    return True
                
                if STATUS.OBSTAC_STOP and STATUS.LOW_COMPUTER_EXIST:
                    # 如果遇到障碍物
                    if STATUS.is_Depth_Obstacle or STATUS.is_Yolo_Obstacle:
                        # 向下位机发送停止信号
                        STATUS.Stop_Publisher.publish('stop')
                        print("\n因为遇到障碍物，向下位机发送停止信号")
                    
                        i = 0
                        while STATUS.is_Depth_Obstacle or STATUS.is_Yolo_Obstacle:
                            time.sleep(0.1)
                            if i % 20 == 0:
                                print("\n语音提示用户避让")
                                text2speech("你好，请让一让", index=1000) # 权益之计：index从0改为1000
                            i += 1
                        
                        STATUS.Navi_target_Publisher.publish(str(STATUS.get_first_Current_Order_of_Visit_id()))  # 向下位机发送导航目标点

        else:
            print(f"开始行走", end='')
            i = 0
            while i < 10:
                # print(f"iiiiiiii: ", i)
                print(f".", end='')
                sleep(0.1)
                i += 1
                if STATUS.is_Interrupted:
                    break
            print(f"机器人停止，共走{i}步")
            return True

class ExplainClass(InterruptClass):
    def __init__(self, qa_class:object):
        super().__init__(qa_class)

        global STATUS
        
        # 可能需要的变量
        self.interrupted = False # 是否被用户语音打断
        self.explanation_completed = False # 讲解是否完整完成

        self.sentences = [] # 用于存储拆分后的所有句子
        self.index_of_sentence = 0 # 记录当前讲解到的句子的索引

    def get_config_explanation_words(self, config_path, hall_index):
        """从配置文件中加载讲解内容。

        Args:
            config_path (str): 配置文件的路径。
            hall_index (int): 展厅的代号。
        """
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        all_speech = config['讲解词列表']
        text = all_speech[STATUS.Index_of_Vist[hall_index]]

        return text

    def split_and_speech_text(self, hall_index):
        """读取文本并按句子拆分。

        Args:
            hall_index (int): 展厅的代号。

        Returns:
            bool: 是否讲解成功。
        """
        STATUS.set_is_Explaining(True)

        self.sentences = []

        # 从配置文件中加载讲解内容
        config_path = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/commentary_config.yaml'

        text = self.get_config_explanation_words(config_path, hall_index) # 从配置文件中加载讲解内容

        splitters = [',', ';', '.','!','?',':', '，', '。', '！', "'", '；', '？', '：', '/'] # 遇到这些符号就拆分句子
        numbers = [str(c) for c in range(10)] # 遇到数字不拆分句子

        sentence = "" # 用于存储句子
        pre_c = '' # 用于存储上一个字符

        # 遍历文本，切分段落为句子
        for c in (text):
            if c == '【':
                if sentence and sentence != ' ':
                    self.sentences.append(sentence)
                sentence = c
                continue
            
            sentence += c
            # 一旦碰到标点符号，就判断目前的长度
            if c in splitters and len(sentence) > 8 + 6:
                if pre_c in numbers:
                    continue
                self.sentences.append(sentence) # 加入句子列表
                sentence = ""
        if sentence:
            self.sentences.append(sentence)
        
        STATUS.SENTENCE_SUM = len(self.sentences)
        
        # 依次播放句子
        if STATUS.TAKE_ACTION_EXPLAIN:
            # 发送讲稿时的起始动作（串行）
            self.request_service_and_send_actions(7, '*')
        
        while self.index_of_sentence < len(self.sentences):
            STATUS.SENTENCE_INDEX = 0
            for STATUS.SENTENCE_INDEX in range(self.index_of_sentence, len(self.sentences)):
                sentence_for_read = self.sentences[STATUS.SENTENCE_INDEX]

                print_flag = False
                if print_flag:
                    print("\t\t\t\t\t\t\t\t\t\t\t\t44444 循环开始等待", datetime.now())
                # 如果上一动作没有执行完，就一直等待
                while not STATUS.EXPLAIN_SHOULD_ACTION:  # Ture就可以跳出循环继续做动作，False就需要一直等
                    # 如果下一句话没有动作就不需要等待
                    if '【' not in sentence_for_read:
                        break

                    if print_flag:
                        print("\t\t\t\t\t\t\t\t\t\t\t\t      正在做动作，等待")
                    continue
                if print_flag:
                    print("\t\t\t\t\t\t\t\t\t\t\t\t55555 等待完毕继续", datetime.now())

                self.index_of_sentence += 1  # 现在讲到的句子的索引加一

                import re

                def find_and_replace_brackets(text):
                    # 使用正则表达式查找并替换【】及其内容
                    pattern = r"【(.*?)】"
                    match = re.search(pattern, text)
                    if match:
                        content = match.group(1)  # 提取括号内的内容
                        # 替换【xxx】为""
                        new_text = re.sub(pattern, "", text)
                        return content, new_text
                        # return content, text
                    else:
                        return None, text
                action_key, sentence_for_read = find_and_replace_brackets(sentence_for_read)

                text2speech(text=sentence_for_read, index=0)  # 0表示异步播放
                # 发送文本到喇叭
                # print(f"{STATUS.SENTENCE_INDEX}: 发送文本到喇叭:", sentence_for_read)

                # 执行讲稿对应的动作
                if action_key and STATUS.TAKE_ACTION_EXPLAIN:
                    action_id = STATUS.ACTOIN_DICT.get(action_key, "没有这个动作")
                    if action_id == "没有这个动作":
                        print("WARNING: 没有找到这个动作: ", action_key)
                    thread.start_new_thread(self.request_service_and_send_actions, (action_id, STATUS.SENTENCE_INDEX, ))
                    if print_flag:
                        print("\t\t\t\t\t\t\t\t\t\t\t\t11111 线程代码之后", datetime.now())
                    sleep(0.15)
                    if print_flag:
                        print("\t\t\t\t\t\t\t\t\t\t\t\t33333 睡眠一下之后", datetime.now())

                if not action_key:
                    if print_flag:
                        print(f"{STATUS.SENTENCE_INDEX}: -------------------------没有动作")
                
                # 处理打断
                interrupt_flag = self.listen_for_INT() # 监听打断信号
                if interrupt_flag:  # 打断后做出的处理
                    # TODO: 如果问答要做动作的话，就需要等待讲稿的动作结束！
                    sleep(0.1)  # 防止 self.handle_interrupt() 太快，在 text2speech 之前把 STATUS.is_interrupted 置为 False
                    if_continue = self.handle_interrupt()  # 调用父类InterruptClass中的方法处理打断

                    if not if_continue: # 不是继续就直接结束讲解
                        STATUS.set_is_Explaining(False)
                        return False
                    
                    else: # 是继续就从上一句没说完的话开始讲
                        text2speech("下面继续讲解", index=0)
                        if self.index_of_sentence > 2:
                            self.index_of_sentence -= 2
                        else:
                            self.index_of_sentence = 0
                        break
                
                # 播放到最后一个句子
                if STATUS.SENTENCE_INDEX == len(self.sentences) - 1:
                    self.explanation_completed = True # 讲解完成
                    self.sentences = [] # 清空句子列表
                    self.index_of_sentence = 0 # 重置句子索引
                    
                    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
                        # 处理打断
                        interrupt_flag = self.listen_for_INT() # 监听打断信号
                        if interrupt_flag:  # 打断后做出的处理
                            # TODO: 如果问答要做动作的话，就需要等待讲稿的动作结束！
                            STATUS.Last_Play_Processor.kill()
                            break
                    
                    break
        
        if self.explanation_completed:
            STATUS.set_is_Explaining(False)
            return True

    def request_service_and_send_actions(self, number=None, index=None):
        print("\t\t\t\t\t\t\t\t\t\t\t\t22222 刚刚进入线程", datetime.now())
        print(f"{index}: -------------------------发送动作数字:", number)

        # 讲解过程中向下位机发送动作指令
        if STATUS.LOW_COMPUTER_EXIST:
            STATUS.EXPLAIN_SHOULD_ACTION = False

            arm_service = rospy.wait_for_service("/doAction") # 等待与下位机通信的服务变得可用
            self.service_client = rospy.ServiceProxy('/doAction', doAction)

            # time.sleep(1)  # 休眠，防止tts空当提前做动作

            try:
                # 向服务发送请求，阻塞，直至做完动作才会返回

                now = datetime.now()
                print(f"{index}: pre send: ",now)

                response = self.service_client(action_code=number)

                now = datetime.now()
                print(f"{index}: post send: ",now)

                print(f"{index}: 动作执行完成:", number)
                print(f"{index}: 返回值:", response)

                STATUS.EXPLAIN_SHOULD_ACTION = True # 可以继续做动作了

            except rospy.ServiceException as e:
                print(f"{index}: 服务调用失败: %s", e)
        else:
            STATUS.EXPLAIN_SHOULD_ACTION = False
            if STATUS.SOUND_OUTPUT_EXIST:
                sleep(1)
            else:
                sleep(1) # 执行动作的时间
            STATUS.EXPLAIN_SHOULD_ACTION = True
                     

class MainClass:
    def __init__(self):
        self.settings()

        # 设置声卡
        STATUS.set_card_id(self.get_card_index_by_keyword('ALC'))
        print("\nSTATUS.card_id: ", STATUS.card_id)

        # 设置麦克
        result = self.set_mic_index_by_keyword('alsa_input.usb-DJI_Technology_Co.__Ltd._Wireless_Microphone_RX-00')
        if result:
            print('mic set success!')
        else:
            print('mic set error')

        # 实例化所有任务的类
        self.qa_class = QAClass()
        self.start = InterruptClass(self.qa_class)
        self.navigation_class = NavigationClass(self.qa_class)
        self.explain_class = ExplainClass(self.qa_class)

        self.temp_last_area = None # 上一个目标点只有在下一次导航开启的时候才会被更新

        rospy.init_node('interrupt', anonymous=True)

        # self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback) # 订阅ivw话题，唤醒词
        if STATUS.SOUND_INPUT_EXIST:
            self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback) # 订阅ivw话题，唤醒词

        if STATUS.FACE_DETECT:
            self.face_detect_queue = []
            self.face_detect_queue_size = 10
            self.face_detect_threshold = 1 - 0.85
            self.face_detect_flag = False
            self.face_sub = rospy.Subscriber("face_chatter", String, self.face_callback)  # 订阅face话题，检测人脸
            
        if STATUS.FACE_RECOGNITION:
            self.face_recog_sub = rospy.Subscriber("face_recogniser", String, self.face_recog_callback)  # 订阅face_recog话题，识别人脸

        if STATUS.OBSTAC_STOP:
            self.obs_sub = rospy.Subscriber("obs_chatter", String, self.obs_callback)  # 订阅obs话题，停障
            self.yolo_sub = rospy.Subscriber("yolo_chatter", String, self.yolo_callback)  # 订阅yolo话题，停障

        if STATUS.POSE_DETECT:
            self.pose_sub = rospy.Subscriber("pose_chatter", String, self.pose_callback)  # 订阅pose话题，手势识别
        
        if STATUS.LOW_COMPUTER_EXIST:
            STATUS.set_Navi_start_Subscriber(rospy.Subscriber("nav_state", String, self.navi_start_callback))  # 导航开始
            STATUS.set_Navi_end_Subscriber(rospy.Subscriber("nav_result", String, self.navi_end_callback))  # 导航结束
            STATUS.set_Navi_target_Publisher(rospy.Publisher("nav_target", String, queue_size=1))  # 导航目标点
            STATUS.set_Stop_Publisher(rospy.Publisher("stop_chatter", String, queue_size=1))  # 导航停止

        print("\033[33mGlobalValues---INFO---\033[0m")
        
        self.welcome()

    def get_card_index_by_keyword(self, keyword):
        # 运行 arecord -l 命令
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error executing arecord -l")
            return None

        # 打印输出结果，方便调试
        # print(result.stdout)

        # 使用正则表达式来查找含有关键字的行，并提取卡片的索引号
        match = re.search(r'card (\d+):.*' + re.escape(keyword), result.stdout)
        if match:
            return int(match.group(1))
        else:
            return None

    def set_mic_index_by_keyword(self, keyword):
        # 运行 arecord -l 命令
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error executing arecord -l")
            return None

        # 打印输出结果，方便调试
        # print(result.stdout)

        # 使用正则表达式来查找含有关键字的行，并提取卡片的索引号
        match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
        if match:
            micid = int(match.group(1))
        else:
            return False
        # 同步执行的 run
        result = subprocess.run(['pactl', 'set-default-source', str(micid)], capture_output=True, text=True)
        return True

    def ivw_callback(self, data):
        # rospy.loginfo(rospy.get_caller_id() + "I heard %s from ivw", data.data)
        # 打断信号置True
        if not STATUS.is_QAing:
            # print(f"打断回调函数接收到打断信号，可以打断")
            print(f"收到打断信号！现在可以打断")
            STATUS.set_is_Interrupted(True)
        else:
            # print(f"打断回调函数接收到打断信号，不可以打断")
            print(f"收到打断信号！现在不可以打断")

    def face_callback(self, data):
        # rospy.loginfo(rospy.get_caller_id() + "I heard %s from face", data.data)
        # print(f"人脸回调函数接收到人脸信号")
        self.face_detect_flag = False

        self.face_detect_queue.append(data.data)
        if len(self.face_detect_queue) >= self.face_detect_queue_size:
            self.face_detect_queue.pop(0)
        r = self.face_detect_queue.count("NOBIGFACE")
        if r / sum(self.face_detect_queue) < self.face_detect_threshold:
            print("ACTIVATE")
            self.face_detect_flag = True

        if data.data == "NOBIGFACE":
            STATUS.set_Big_Face_Area("NOBIGFACE")
        elif data.data == "LEFT":
            STATUS.set_Big_Face_Area("LEFT")
        elif data.data == "RIGHT":
            STATUS.set_Big_Face_Area("RIGHT")
        else:
            STATUS.set_Big_Face_Area("CENTER")
            
        if self.face_detect_flag:
            STATUS.set_is_Big_Face_Detected(True) # 检测到(居中)人脸
        else:
            STATUS.set_is_Big_Face_Detected(False) # 没有检测到(居中)人脸，需要转向
            
    def face_recog_callback(self, data):
        face_name_list_from_string = ast.literal_eval(data.data)
        face_name_list_by_dict = [STATUS.Face_Name_Dict[item] for item in face_name_list_from_string]
        # print(f"face_name_list_from_string: {face_name_list_from_string}")
        if len(face_name_list_by_dict) > 0:
            STATUS.set_Face_Name_list(face_name_list_by_dict)
            STATUS.set_is_Face_Recognized(True)
        
    def obs_callback(self, data):
        if data.data == '++++':
            if STATUS.is_Depth_Obstacle == False:
                print(f"深度回调函数接收到障碍物信号")
            STATUS.set_is_Depth_Obstacle(True)
        else:
            STATUS.set_is_Depth_Obstacle(False)

    def yolo_callback(self, data):
        if data.data == '++++':
            if STATUS.set_is_Yolo_Obstacle(False):
                print(f"YOLO回调函数接收到障碍物信号")
            STATUS.set_is_Yolo_Obstacle(True)
            STATUS.set_COUNT_YOLO(0)
        else:
            STATUS.set_COUNT_YOLO (STATUS.COUNT_YOLO+1)  
            # print("STATUS.COUNT_YOLO: ", STATUS.COUNT_YOLO)       
            if STATUS.COUNT_YOLO > 10:
                STATUS.set_is_Yolo_Obstacle(False)
                STATUS.set_COUNT_YOLO(0)

    def pose_callback(self, data):
        STATUS.set_POSE_DETECT_KEYWORD(data.data )
        
    def navi_start_callback(self, data):
        STATUS.set_NAVI_START_FLAG(data.data)
        # print(data)
        # print(data.data)
        
    def navi_end_callback(self, data):
        STATUS.set_NAVI_END_FLAG(data.data)
        # print(data)
        # print(data.data)

    # TODO: 让GPT4对文本进行切分并匹配动作（动作的执行时间应该与文本的播音时间匹配）尤其是说到数字时伸手指
    # TODO: 加上手势识别

    def settings(self):
        # 设置所有功能开关
        STATUS.set_TAKE_ACTION_QA(False)        # 问答时是否要做动作
        STATUS.set_TAKE_ACTION_EXPLAIN(False)   # 讲稿时是否要做动作
        STATUS.set_FACE_DETECT(False)           # 人脸检测
        STATUS.set_FACE_RECOGNITION(False)      # 人脸识别
        STATUS.set_OBSTAC_STOP(False)           # 停障
        STATUS.set_POSE_DETECT(False)           # 姿势检测

        # 选择大语言模型
        STATUS.set_MODEL_TASK_TYPE('qwen1_5')   # chatglm gpt-4 gpt-3.5-turbo qwen1_5
        STATUS.set_MODEL_LLM_ANSWER('qwen1_5')    # huozi gpt-4 chatglm qwen1_5
        STATUS.set_STREAM_RETURN(True)          # 是否使用流式返回
        STATUS.set_MODEL_BAN_OPENAI(False)      # OPENAI是否不可用

        # 硬件设备情况
        STATUS.set_LOW_COMPUTER_EXIST(False)    # 下位机是否存在
        STATUS.set_SOUND_INPUT_EXIST(True)     # 录音设备是否存在
        STATUS.set_SOUND_OUTPUT_EXIST(True)    # 播音设备是否存在

        # 录音参数
        STATUS.set_DURATION(10)                  # 无人说话时每轮录音的时间
        STATUS.set_THRESHOLD_AUDIO(25)           # 超过该音量阈值识别到有人讲话

        # 在禁用OpenAI的情况下，会启用旧版问答程序
        if STATUS.MODEL_BAN_OPENAI:
            STATUS.set_MODEL_TASK_TYPE('chatglm')
            STATUS.set_MODEL_LLM_ANSWER('chatglm')

        STATUS.print_all_status()
    
    def welcome(self, ):
        
        # print("进入welcome阶段")

        # 人脸检测唤醒，注意不要和语音唤醒同时开启
        if STATUS.FACE_DETECT:
            while True:
                if STATUS.is_Big_Face_Detected:
                    break
        
        # 人脸识别迎宾
        if STATUS.FACE_RECOGNITION and len(STATUS.Face_Name_list) > 0:
            while True:
                if STATUS.is_Face_Recognized:
                    face_name_join_str = '、'.join(STATUS.Face_Name_list)
                    if len(STATUS.Face_Name_list) == 1:
                        hello_str = '你好'
                    else:
                        hello_str = '你们好'
                    text2speech(f"{face_name_join_str}，{hello_str}！", index=1000)
                    # STATUS.set_is_Face_Recognized(False)
                    
                    break
        
        STATUS.set_is_QAing(True)
        text2speech("各位游客大家好，请说，小红小红", index=1000)
        # text2speech("各位游客大家好，欢迎来到机器人实验室，我是展厅机器人，小红，如果需要我带您参观机器人实验室，请说，小红小红", index=1000)
        time.sleep(1)
        STATUS.set_is_Interrupted(False)
        STATUS.is_Interrupted = False
        STATUS.set_is_QAing(False)
        
        # 麦克风不可用，手动唤醒
        # msg = String('小红小红')
        # self.ivw_callback(msg)
        
        # 语音唤醒
        while STATUS.SOUND_INPUT_EXIST:
            if STATUS.is_Interrupted:
                STATUS.is_Interrupted = False
                break
        
        STATUS.set_is_QAing(True)
        if STATUS.FACE_RECOGNITION:  # 如果开启人脸识别，会和检测到的人问好，就不用说大家好了
            text2speech("我是小红。", index=1000)
        else:
            text2speech("大家好，我是小红。", index=1000)
        time.sleep(1)
        STATUS.set_is_QAing(False)

        # sleep(0.5)
        # text2speech("好的。大家好，我是小红，很荣幸接下来能由我带领大家参观机器人展厅。", index=0)

        self.main()
        
    def main(self, ):
        while True:
            next_destination = STATUS.get_first_Current_Order_of_Visit_id() # 获取下一个目标点
            
            print_flag = False
            if next_destination != None: # 如果还有目标点，执行导航
                if print_flag:
                    print("\t\t\t\t\t\t\t\t\t\t\t\t44444 循环开始等待", datetime.now())
                # 如果上一动作没有执行完，就一直等待
                while not STATUS.EXPLAIN_SHOULD_ACTION:  # Ture就可以跳出循环继续做动作，False就需要一直等
                    if print_flag:
                        print("\t\t\t\t\t\t\t\t\t\t\t\t      正在做动作，等待")
                    continue
                if print_flag:
                    print("\t\t\t\t\t\t\t\t\t\t\t\t55555 等待完毕继续", datetime.now())

                # text2speech(f"下面带大家参观{STATUS.Current_Order_of_Visit[0]}", index=1000)
                # TODO: 按照 ExplainClass 类的逻辑处理引导词的打断
                STATUS.set_is_QAing(True)
                text2speech(f"{STATUS.TRANSITIONAL_SENTENCE[next_destination]}", index=1000)
                time.sleep(0.2)
                STATUS.set_is_QAing(False)

                transitional_action = STATUS.TRANSITIONAL_ACTION[next_destination]
                if transitional_action and STATUS.TAKE_ACTION_EXPLAIN:
                    # 过渡句的动作（串行）
                    self.explain_class.request_service_and_send_actions(
                        number=STATUS.ACTOIN_DICT.get(transitional_action),
                        index='*'
                        )
                
                print(f"\n执行去往 {next_destination} 号目标点的导航\n")

                if next_destination != 0:
                # if next_destination == -1:  # 关闭导航
                    if STATUS.TAKE_ACTION_EXPLAIN:
                        # 恢复直立状态（串行）
                        self.explain_class.request_service_and_send_actions(21, '*')
                    
                    STATUS.set_Last_Area(self.temp_last_area) # 下一次导航开始时，记录上一次导航的目标点

                    if_success_navigate = self.navigation_class.send_destination_and_handle_interrupt(next_destination) # 向下位机发送导航目标点

                    # print("interrupt_navigation正常跳出")
                    # print("\nif_success_navigate: ", if_success_navigate)

                else: 
                    if_success_navigate = True

                if if_success_navigate: # 如果导航成功，执行讲解
                    # 修改当前位置
                    self.temp_last_area = STATUS.Current_Order_of_Visit.pop(0)
                    STATUS.Current_Area = STATUS.Index_of_Vist[next_destination]

                    print(f"\n执行位于 {next_destination} 号目标点的讲解\n")

                    if_success_explain = self.explain_class.split_and_speech_text(next_destination) # 启动讲解

                    # print("\nif_success_explain: ", if_success_explain)
                    if if_success_explain: # 如果讲解成功，执行问答
                        print(f"\n执行位于 {next_destination} 号目标点的问答\n")

                        self.start.handle_interrupt()
                
                # 重置flag值
                if_success_navigate = False
                if_success_explain = False

            else: # 如果没有目标点了，全流程结束
                break

        text2speech("参观到此结束，欢迎再来哈工大找我玩。", index=1000)
        print("任务结束")
    
if __name__ == "__main__":
    main_class = MainClass()