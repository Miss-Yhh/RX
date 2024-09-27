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

# from kedaxunfei_iat.iat_as_service_iter import iat_web_api  # 
# from kedaxunfei_iat.iat_as_service import iat_web_api
# from kedaxunfei_iat.test_webapi_iat_stream import iat_web_api  # 科大讯飞公有云
# from kedaxunfei_iat.test_host_3090_iat import iat_web_api  # 科大讯飞私有云-没有流式
# from kedaxunfei_iat.test_host_3090_iat_stream import iat_web_api  # 科大讯飞私有云-流式
# from tencentclound.tencentclound import iat_tencent as iat_web_api
from test_host_3090_iat import iat_web_api, kedaxunfei_iat_service
import rospy
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
try:
    from harbin_pkg.srv import moveToTarget   # 下位机移动服务
    from harbin_pkg.srv import doAction       # 下位机动作服务
    from harbin_pkg.msg import stopProcessing # 下位机暂停话题
except:
    pass
    # print("failed to import ..")
    
from GlobalValues import GlobalValuesClass
from interrupt.PPL.api import get_task_type, get_llm_answer, get_visit_destination, get_action_type, get_anaphora_result
# from Only_text_prompt.Robot_prompt_text import ask  #lhkong动作分类

STATUS = GlobalValuesClass(name="Anythin is OK")
STATUS_DICT = STATUS.get_states_dict()

# print(STATUS.is_Explaining)
# print(STATUS_DICT)

def text2speech(text='', index=0, is_beep=False, wavfile=None, ignore_interrupt=False):
    # 如果喇叭不存在就直接跳过
    if not STATUS.SOUND_OUTPUT_EXIST:
        print(f"喇叭不存在: {text}")
        sleep(1)
        return

    savepath = os.path.join('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech', str(time.time())+'.wav')
    if not wavfile:
        ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
        while ttsproc.poll() is None:
            # print(f'tts process is working, interrupted:--{STATUS.is_Interrupted}--, 时间: {datetime.now()}, 本句是:{text}')
            
            # print('waiting tts...')
            if STATUS.is_Interrupted:
                # print("not kill tts and just break")
                # ttsproc.kill()
                # tts需要释放资源，不能用kill杀掉进程，需要断开链接，否则连续打断多次之后tts服务会卡死
                break
            
            # time.sleep(0.1)
            
        # print('after waiting tts')  
    
    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        # print(f'last process is working, waiting, 时间: {datetime.now()}, 本句是:{text}')
        
        if STATUS.is_Interrupted:
            print(f"播音被打断，杀死上一句播音的进程..{datetime.now()}.本句是:{text}")
            print("kill last play")
            STATUS.Last_Play_Processor.kill()
            if not ignore_interrupt:
                return None
            else:
                break
            
        # time.sleep(0.3)
    
    # 对于第一句来说，没有上一句，不会进入上面的循环，需要独立判断有没有打断
    if STATUS.is_Interrupted:
        if not ignore_interrupt:
            return None
        
    if text:  # 在确定会播音之后记录正在播音的话
        if is_beep:
            STATUS.set_LAST_BROAD_WORDS(STATUS.LAST_BROAD_WORDS + text)
        else:
            STATUS.set_LAST_BROAD_WORDS(text)
    
    print(f"正在播音...({text})")
    if wavfile:
      savepath = wavfile
    savepath_louder = savepath.replace('.wav', 'louder.wav')
    cmd = f"ffmpeg -loglevel quiet -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -filter:a \"volume={STATUS.SOUND_CHANGE}dB\" -y {savepath_louder}"
    _ = os.system(cmd)
    if STATUS.card_id == -1:
      playproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/play_sound.py", savepath_louder])
    else:
      # os.system('amixer -c 0 set Master 100%')
      playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", f'{savepath_louder}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            # print(f'play process is working, 时间: {datetime.now()}, 本句是:{text}')
            if STATUS.is_Interrupted and not ignore_interrupt:
                print(f"播音被打断，杀死正在同步播放的的进程...本句是:{text}")
                print('kill play process')
                playproc.kill()
                return
            # time.sleep(0.3)
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
    
    repeat_count = 0  # 提示用户现在可以提问的次数
    while True:
        userword = listenuser('ding', iter=pardon_round)
        
        if userword and userword != '####':
            break
        elif userword == '####' or repeat_count < 1:
            print('大家现在可以向我提问', datetime.now())
            text2speech("大家现在可以向我提问", index=1000, is_beep=True, wavfile='/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/canaskme.wav')  # 用户超过 6 秒没有说话就询问一遍
            repeat_count += 1
        else:
            STATUS.set_is_QAing(False)
            while True:
                # 处理打断
                if STATUS.is_Interrupted:  # 打断后做出的处理
                    STATUS.set_is_Interrupted(False)
                    text2speech("大家现在可以向我提问", index=1000, is_beep=True, ignore_interrupt=True, wavfile='/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/canaskme.wav')  # 用户超过 6 秒没有说话就询问一遍
                    break
                
        STATUS.set_is_QAing(True)
        STATUS.set_is_Interrupted(False)
            

    # print(f"录制结束，录制结果为: {userword}")
    
    # text2speech("好的", index=0, is_beep=True)
    # userword = input()
    return userword

def record_speech_recognition(recognition_result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/SpeechRecognition.txt', 'a') as f:
        f.write(f"时间：{current_time}\n")
        f.write(f"上一句播音的话：{STATUS.LAST_BROAD_WORDS}\n")
        f.write(f"语音识别结果：{recognition_result}\n\n")
        
def record_task_classification(user_command, classification_result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/TaskClassification.txt', 'a') as f:
        f.write(f"时间：{current_time}\n")
        f.write(f"用户指令：{user_command}\n")
        f.write(f"分类结果：{classification_result}\n\n")

def record_question_answer(old_question, old_complete_answer, question, document, answer):
    with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/QuestionAnswer.txt', 'a') as f:
        f.write(f"上一轮问题：{old_question}\n")
        f.write(f"上一轮回答：{old_complete_answer}\n")
        f.write(f"问题：{question}\n")
        f.write(f"回答：{answer}\n")
        f.write(f"文档：{document}\n\n")
        
def task_class_result_replace(result):
    if '问答' in result:
        if '明确' in result:
            return 'qa explicit'
        else:
            return 'qa'
    elif '参观' in result:
        result = result.replace("参观", "visit")
        return result
    elif '休眠' in result:
        return 'sleep'
    elif '音量变大' in result:
        return 'soundbig'
    elif '音量变小' in result:
        return 'soundsmall'
    elif '继续' in result:
        return 'continue'
    else:
        return 'bad continue'

class InterruptClass:
    def __init__(self, qa_class:object):
        global STATUS
        
        self.qa_class = qa_class  # 传入的问答类实例用于生成用户问题的回答
        
        self.pre_next_situation = False  # 是否出现参观目标点中包含“上一个”或“下一个”的情况

    def listen_for_INT(self, ) -> bool:
        """监听打断信号, 返回是否打断
        
        """
        return STATUS.is_Interrupted
    
    def continue_rotate(self, rotate='left'):
        if rotate == 'middle':
            print("此处不需要转向寻找人脸.")
        else:
            print("转向寻找人脸ing...")
            try:
                # 设置发布频率
                rate = rospy.Rate(30)  # 30hz

                # 创建Twist消息实例
                move_cmd = Twist()
                
                # 预备
                move_cmd.angular.z = 0.0
                STATUS.Rotate_Publisher.publish(move_cmd)
                
                rate.sleep()
                
                speed = 0.5 if rotate == 'left' else -0.5
                move_cmd.angular.z = speed
                
                STATUS.set_Big_Face_Area(None)
                
                # 方案1. 识别到任何人都可以
                # while STATUS.FACE_DETECT and not STATUS.Big_Face_Area:
                #     STATUS.Rotate_Publisher.publish(move_cmd)
                #     rate.sleep()
                    
                # 方案2. 识别到手持麦克风就可以
                while STATUS.HANDHELD_DETECT and not STATUS.HANDHELD_DETECT_FLAG:
                    STATUS.Rotate_Publisher.publish(move_cmd)
                    rate.sleep()
                    
                print(f"转向找到人脸")

            finally:
                # 停止
                move_cmd.angular.z = 0.0
                STATUS.Rotate_Publisher.publish(move_cmd)
                
    def do_action_rely_instruction(self, question=""):
        action_type = get_action_type(question)
        action_index = None

        for one_of_every_action, one_of_every_action_index in \
        zip(['前进', '后退', '左转', '右转'], [101, 102, 103, 104]):
            if one_of_every_action in action_type:
                action_type = one_of_every_action
                action_index = one_of_every_action_index
        
        if action_index == None:
            print(f"动作分类大模型分类失败！输出结果：{action_type}")
            # text2speech(f"对不起，这个动作我还不会，我只会向前走、向后走、向左转或者向右转", index=1000)
        else:
            if STATUS.LOW_COMPUTER_EXIST:
                print(f"执行动作：{action_type}")
                STATUS.Navi_target_Publisher.publish(str(action_index))
                
                while True:
                    if STATUS.NAVI_END_FLAG == 'success':
                        STATUS.set_NAVI_END_FLAG(None)
                        break
            else:
                print(f"执行动作：{action_type}")

    def handle_interrupt(self, ):
        """处理所有情况下用户打断的操作。

        """
        name = self.get_self_name() # 获取调用该方法的类的名称，例如NavigationClass, ExplainClass等
        print(f"\n处理 {name} 过程中的打断")
        
        STATUS.set_is_QAing(True) # 防止问答被打断 - 开始

        if STATUS.HANDHELD_DETECT and STATUS.LOW_COMPUTER_EXIST:
            if 'InterruptClass' not in name:
                if 'NavigationClass' in name:  # 由于机器人贴着右边墙走，所以导航中打断向左转
                    rotate = 'left'
                else:
                    rotate = STATUS.Trun_Direction.get(STATUS.Current_Area, 'left')
                self.continue_rotate(rotate=rotate)
        
        task = 'qa'
        toupad_target = ""  # 将触摸屏目标点置为空
        clear = True # 是否清楚展品名称
        
        pre_next_flag = True
        while pre_next_flag: # 该循环的唯一作用是：如果不存在'下一个'或'上一个'展区，机器人会提示用户重新下达指令，此时程序会跳转到该循环的开始处
            pre_next_flag = False

            # 一直进行问答，直到task不是QA，转而进行其他操作
            while "qa" in task:
                sleep(0.05)
                
                # 播放以下提示音的条件：1.展品清晰；2.被打断；3.没有上一个、下一个情况
                print(f"播放“大家有什么问题吗？”提示音的条件: |--{clear}--{self.qa_class.interrupt_stream}--{self.pre_next_situation}--|")
                
                if clear and self.qa_class.interrupt_stream and not self.pre_next_situation:
                    anybodyquestions = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/anybodyquestionss.wav'
                    iamhere = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/iamhere.wav'
                    print("In InterruptClass.handle_interrupt 接下来使用text2speech播音“大家有什么问题吗？”")
                    if 'InterruptClass' in name:
                        text2speech('大家有什么问题或指令吗？', index=1000, is_beep=True, wavfile=anybodyquestions, ignore_interrupt=True) # 提示用户说出问题
                    else:
                        print(f"我在之前STATUS.is_Interrupted:{STATUS.is_Interrupted}")
                        text2speech('我在', index=0, is_beep=True, wavfile=iamhere, ignore_interrupt=True) # 提示用户说出问题
                
                STATUS.set_is_Interrupted(False)
                    
                self.pre_next_situation = False
                self.qa_class.interrupt_stream = True

                STATUS.set_Touchpad_Area('NowIsInterrupted')
                
                question = pardon() # 录制用户的指令
                # print(f"\n用户指令: {question}\n")
                
                # 用户没有点击触控屏
                if STATUS.Touchpad_Area == 'NowIsInterrupted':
                    STATUS.set_Touchpad_Area('NowIgnoreTouchpad')

                    # 使用任务分类大模型
                    task_result = get_task_type(text=question,
                                                exhibition=STATUS.Current_Area,
                                                extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""),
                                                model=STATUS.MODEL_TASK_TYPE)  # 任务分类
                    task = task_class_result_replace(task_result)
                    record_task_classification(question, task)
                    print('------task 任务判断结束时间=', datetime.now())
                    
                # 用户点击了触控屏
                else:
                    toupad_target = STATUS.Abb_of_Visit[STATUS.Touchpad_Area]
                    task = "visit"

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

                if STATUS.Touchpad_Area == 'NowIgnoreTouchpad' and task == 'qa':
                    if clear: # 如果清楚展品名称，就直接回答
                        STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
                        
                        if STATUS.TAKE_ACTION_QA:
                            # 开启线程 做动作
                            self.doaction_thread = threading.Thread(target=self.do_action_rely_instruction, args=(question,)) # 初始化做动作的线程
                            self.doaction_thread.start()  # 启动做动作的线程
                        
                        self.qa_class.answer_question(question) # 生成答案并播音
                        
                        if STATUS.TAKE_ACTION_QA:
                            self.doaction_thread.join()  # 等待做动作的线程
                        
                        STATUS.set_is_QAing(True) # 防止问答被打断 - 开始
                    else:
                        text2speech('大家还有其他问题吗？', index=1000, is_beep=True)

            if 'visit' in task:
                STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
                
                if toupad_target:  # 如果用户点击了触摸屏，则已经确定目标点
                    target_point = toupad_target
                else:  # 如果用户通过语音下达指令，使用大模型提取目标点
                    if '上一个' in question:
                        target_point = '上一个'
                    elif '下一个' in question:
                        target_point = '下一个'
                    else:
                        target_point = get_visit_destination(question)
                
                print('导航点名称：', target_point)

                # TODO: 思考不同任务过程中的新导航指令是否需要不同的处理（可能与更改目标点列表策略有关）

                if target_point:
                    if '下一个' in target_point: # 去往下一个展区
                        now_destination = STATUS.Current_Order_of_Visit[0]  # 记录当前展区
                        
                        # 使用正则表达式匹配基础前缀和可能的数字后缀
                        match = re.match(r"^(.+?)(_?\d*)$", now_destination)
                        if match:
                            prefix = match.group(1)  # 基础前缀
                            suffix = match.group(2)  # 数字后缀，可能为空
                        else:
                            prefix = now_destination
                            suffix = ''
                            
                        def remove_items_prefix(prefix):
                            # 遍历列表，删除符合前缀条件的元素，直到遇到不符合条件的元素
                            index = 0
                            while index < len(STATUS.Current_Order_of_Visit):
                                item = STATUS.Current_Order_of_Visit[index]
                                # 检查是否以基础前缀开始
                                if item.startswith(prefix):
                                    STATUS.Current_Order_of_Visit.pop(index)
                                    # 因为删除了元素，所以不需要增加索引
                                else:
                                    # 一旦遇到第一个不符合条件的元素，停止遍历
                                    break

                        if 'NavigationClass' in name: # 如果是导航中被打断
                            
                            remove_items_prefix(prefix=prefix)
                            
                            if len(STATUS.Current_Order_of_Visit) > 0: # 下一个展区是目标点列表中的第二个展区（不过第一个展区已经被pop出去了）
                                # text2speech(f"那我们跳过{now_destination}，前往下一个展区，{STATUS.Current_Order_of_Visit[0]}", index=0)
                                STATUS.set_Destination_Area(new_Destination_Area=STATUS.Current_Order_of_Visit[0])

                            else: # 如果已经没有下一个展区
                                text2speech(f"不好意思，{now_destination}已经是最后一个展区，请您告诉我，想去哪个展区还是继续去{now_destination}", index=1000)
                                pre_next_flag = True
                                self.pre_next_situation = True
                                task = 'qa'
                                STATUS.set_is_Interrupted(False)
                                continue
                        
                        else: # 如果并非导航过程中被打断，说明上一次导航已经结束
                            
                            if '_' in now_destination:
                                remove_items_prefix(prefix=prefix)

                            if len(STATUS.Current_Order_of_Visit) > 0: # 下一个展区是目标点列表中的第一个展区
                                # text2speech(f"前往下一个展区，{STATUS.Current_Order_of_Visit[0]}", index=0)
                                STATUS.set_Destination_Area(new_Destination_Area=STATUS.Current_Order_of_Visit[0])
                            
                            else: # 如果已经没有下一个展区
                                text2speech(f"不好意思，{STATUS.Current_Area}已经是最后一个展区，请您向我提问或告诉我您要去哪个展区", index=1000)
                                pre_next_flag = True
                                self.pre_next_situation = True
                                task = 'qa'
                                STATUS.set_is_Interrupted(False)
                                continue
                    
                    elif '上一个' in target_point:  # 去往上一个展区

                        if STATUS.Last_Area: # 如果有上一个展区的话
                            # text2speech(f"那我们回到上一个展区，{STATUS.Last_Area}", index=0)
                            STATUS.set_Destination_Area(new_Destination_Area=STATUS.Last_Area)

                        else: # 如果没有上一个展区
                            text2speech(f"不好意思，我们还没有参观过其他展区，请您向我提问或告诉我您要去哪个展区", index=1000)
                            pre_next_flag = True
                            self.pre_next_situation = True
                            task = 'qa'
                            STATUS.set_is_Interrupted(False)
                            continue
                        
                    else: # 不是'下一个'或'上一个'，而是直接给出目标点名称
                        if target_point == '开始位置':
                            return 'start'
                        
                        if target_point == "NotInArrage" or target_point == '其他':
                            text2speech("不好意思，我没有听清您的指令，请您再说一遍！", index=1000)
                            pre_next_flag = True
                            self.pre_next_situation = True
                            task = 'qa'
                            STATUS.set_is_Interrupted(False)
                            continue
                            
                        for one_of_every_target in STATUS.Origin_Order_of_Visit:
                            if one_of_every_target in target_point:
                                target_point = one_of_every_target
                        STATUS.set_Destination_Area(new_Destination_Area=target_point)
            
            elif 'sleep' in task:
                STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
                STATUS.set_Destination_Area(new_Destination_Area="参观起始位置")
            
            elif 'soundbig' in task:
                # os.system('amixer -c 0 set Master 10%+')
                STATUS.set_SOUND_CHANGE(STATUS.SOUND_CHANGE+3)
                text2speech("我已经为您调大音量，您还有其他问题吗", index=1000)
                pre_next_flag = True
                self.pre_next_situation = True
                task = 'qa'
                STATUS.set_is_Interrupted(False)
                continue
                
            elif 'soundsmall' in task:
                # os.system('amixer -c 0 set Master 10%-')
                STATUS.set_SOUND_CHANGE(STATUS.SOUND_CHANGE-3)
                text2speech("我已经为您调小音量，您还有其他问题吗", index=1000)
                pre_next_flag = True
                self.pre_next_situation = True
                task = 'qa'
                STATUS.set_is_Interrupted(False)
                continue
            
            elif 'continue' in task:
                STATUS.set_is_QAing(False) # 防止问答被打断 - 结束
                return 'continue'

            else:
                pass

        # 如果有明确的visit指令，或者导航过程被打断后的continue指令，那就打印将要去的目标点
        if 'visit' in task or ('NavigationClass' in name and 'continue' in task):
            # print("\n即将去往: ", STATUS.Destination_Area)
            print("\n目前的目标点列表: ", STATUS.Current_Order_of_Visit)

        STATUS.set_is_QAing(False) # 防止问答被打断 - 结束

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
        self.qaclass_thread = threading.Thread(target=self.QAClassInit,) # 初始化问答模型的线程
        self.qaclass_thread.start()  # 启动问答模型的初始化
        
        self.interrupt_stream = True  # 标志着流式返回的问答 被打断，而不是正常退出
        self.task_type_label_list = ['参观', '休眠', '继续']
        
        self.complete_answer = ""
    
    def QAClassInit(self):
        LLMClass = get_llm_answer(model=STATUS.MODEL_LLM_ANSWER, stream_bool=STATUS.STREAM_RETURN)
        self.llmclass = LLMClass
    
    def answer_question(self, user_words:str) -> str:
        # STATUS.set_is_QAing(True)

        # text2speech("请稍等，让我思索一下。", index=0)
        
        # 文档检索问答模型初始化完成
        self.qaclass_thread.join()
        self.interrupt_stream = False
        
        # 随机说‘好’或‘好的’
        guodus = ['好', '好的']
        a, b = 0, len(guodus)
        choice = random.randint(a,b-1)
        text = guodus[choice]
        wavfile = f'/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/{text}.wav'
        text2speech(text=text, index=0, wavfile=wavfile)
        
        # 检测游客指令中是否出现指代消解现象，即没有具体对象
        
        # anaphora_result = get_anaphora_result(query=user_words)
        # print("大模型 - 出现指代消解问题了吗: ", anaphora_result)
        anaphora_result = '否'
        
        if '是' in anaphora_result:
            if_anaphora = True
        else:
            if_anaphora = False
        # print("wmjwmj, 即将进入问答", STATUS.Current_Order_of_Visit)
        if STATUS.STREAM_RETURN:
            splitters = [',', ';', '.', '!', '?', ':', '，', '。', '！', "'", '；', '？', '：', '/', '\n']
            numbers = [str(c) for c in range(10)]
            
            buffer = ""  # 初始化缓存字符串
            for qa_answer in self.llmclass.process_query(
                query=user_words,
                if_anaphora=if_anaphora,
                exhibition=STATUS.Current_Area,
                extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""),
                commentary_speech=STATUS.COMMENTARY_SPEECH,
                ):
                if STATUS.is_Interrupted:  # 受到打断直接退出此次问答
                    record_question_answer(
                        old_question=self.llmclass.old_question,
                        old_complete_answer=self.llmclass.old_complete_answer,
                        question=user_words, 
                        document=self.llmclass.now_document,
                        answer=self.complete_answer)
                    
                    if self.llmclass.if_document_searched:
                        self.llmclass.old_question = user_words
                        self.llmclass.old_complete_answer = self.complete_answer
                    self.complete_answer = ""
                    self.interrupt_stream = True
                    
                    break  # 跳出此次回答，忽略剩余的模型回答
                
                if qa_answer:
                    # qa_answer = qa_answer.replace('A', '诶') if 'A' == qa_answer else qa_answer
                    
                    self.complete_answer += qa_answer
                    
                    buffer += qa_answer  # 将流式返回的结果累加到缓存中

                    # 检查最后一个字符是否是分隔符，并且缓存长度大于5
                    # if buffer[-1] in splitters and len(buffer) > 8:
                    if buffer[-1] in splitters:
                        # if len(buffer) > 1 and buffer[-2] in numbers:
                        #     continue  # 如果分隔符前是数字，继续累积缓存

                        # 由于使用了qwen，就不用拦截了
                        # if '根据' not in buffer and '参考' not in buffer:
                        #     print("将大模型回答发送到喇叭:", buffer)
                        #     text2speech(buffer, index=0)  # 播放缓存中的内容
                        # else:
                        #     print("拦截类似 根据参考文本 的句子:", buffer)
                        print(f'+++++++++语音合成：{buffer}\n语音合成开始', datetime.now())
                        text2speech(buffer, index=0)
                        buffer = ""  # 清空缓存
                else:
                    # print("生成器生成 None 字符")
                    pass
            
            if not self.interrupt_stream:  # 没有被打断
                if buffer:  # 如果循环结束后缓存中还有内容，也播放它
                    # print("将大模型回答发送到喇叭:", buffer)
                    text2speech(buffer, index=1000)
                else:
                    text2speech("？", index=1000)
                  
                record_question_answer(
                    old_question=self.llmclass.old_question,
                    old_complete_answer=self.llmclass.old_complete_answer,
                    question=user_words, 
                    document=self.llmclass.now_document,
                    answer=self.complete_answer)
                
                if self.llmclass.if_document_searched:
                    self.llmclass.old_question = user_words
                    self.llmclass.old_complete_answer = self.complete_answer
                self.complete_answer = ""
            
        else:  # 被打断
            qa_answer = self.llmclass.process_query(
                user_words,
                if_anaphora=if_anaphora,
                exhibition=STATUS.Current_Area,
                extra_information=STATUS.EXTRA_INFORMATION.get(STATUS.Current_Area, ""),
                commentary_speech=STATUS.COMMENTARY_SPEECH,
                ) # 问答模型处理用户问题
            
            record_question_answer(
                old_question=self.llmclass.old_question,
                old_complete_answer=self.llmclass.old_complete_answer,
                question=user_words, 
                document=self.llmclass.now_document,
                answer=qa_answer)
            
            if self.llmclass.if_document_searched:
                self.llmclass.old_question = user_words
                self.llmclass.old_complete_answer = qa_answer

            print("将大模型回答发送到喇叭:", qa_answer)
            text2speech(qa_answer, index=1000) # 语音回答用户问题
        
        if self.interrupt_stream:
            sleep(0.05)
            STATUS.set_is_Interrupted(False)
        else:
            pass
            # text2speech('我说完了，大家还有问题吗？', index=1000, is_beep=True)
            
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
                if wait_for_naiv_start > 50:
                    print("导航启动话题没有响应！")
                    STATUS.set_is_Navigating(False)
                    return False
                
                if STATUS.NAVI_START_FLAG == 'active':  # 导航顺利启动
                    print("导航顺利启动!")
                    break
                elif STATUS.NAVI_START_FLAG == 'busy':  # 导航启动失败
                    print("导航启动失败！move base不可用！")
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
                    if if_continue not in ['continue', 'start']: # 不是继续就直接结束导航
                        STATUS.set_is_Navigating(False)
                        if '_' not in STATUS.Current_Order_of_Visit[0]:  # 只有非额外目标点才能被记录
                            STATUS.set_Last_Area(STATUS.Current_Order_of_Visit[0])
                        return False
                    else: # 是继续就继续导航
                        return False
                    
                # 如果成功到达指定地点
                # print("STATUS.NAVI_END_FLAG:", STATUS.NAVI_END_FLAG)
                if STATUS.NAVI_END_FLAG == 'success':
                    STATUS.set_is_Navigating(False)
                    STATUS.set_NAVI_END_FLAG(None)
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
            # while i < 100:
            while i < 10:
                # print(f"iiiiiiii: ", i)
                print(f"\r开始行走{'.'*i}", end='')
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
        self.interrupted = False  # 是否被用户语音打断
        self.explanation_completed = False  # 讲解是否完整完成
        self.WaitUtil = False  # 是否进入过静默等待模式

        self.sentences = [] # 用于存储拆分后的所有句子
        self.index_of_sentence = 0 # 记录当前讲解到的句子的索引

    def get_config_explanation_words(self, config_path, hall_name):
        """从配置文件中加载讲解内容。

        Args:
            config_path (str): 配置文件的路径。
            hall_name: 展区的名字。
        """
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        all_speech = config['讲解词列表']
        text = all_speech[hall_name]

        return text

    def split_and_speech_text(self, hall_name):
        """读取文本并按句子拆分。

        Args:
            hall_name: 展区的名字。

        Returns:
            bool: 是否讲解成功。
        """
        STATUS.set_is_Explaining(True)
        
        self.sentences = [] # 清空句子列表
        self.index_of_sentence = 0 # 重置句子索引

        # 从配置文件中加载讲解内容
        if STATUS.ROBOT_NAME == 'X':
            config_path = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/X_讲稿.yaml'
        elif STATUS.ROBOT_NAME == 'K':
            config_path = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/K_讲稿.yaml'

        text = self.get_config_explanation_words(config_path, hall_name) # 从配置文件中加载讲解内容

        splitters = [',', ';', '.','!','?',':', '，', '。', '！', "'", '；', '？', '：', '/'] # 遇到这些符号就拆分句子
        numbers = [str(c) for c in range(10)] # 遇到数字不拆分句子

        sentence = "" # 用于存储句子
        pre_c = '' # 用于存储上一个字符

        # 遍历文本，切分段落为句子
        for c in (text):
            if c == '【' or c == '〖':
                if sentence and sentence != ' ':
                    self.sentences.append(sentence)
                sentence = c
                continue
            
            sentence += c
            
            # 一旦碰到标点符号，就判断目前的长度
            if c == '〗':
                self.sentences.append(sentence) # 加入句子列表
                sentence = ""
                
            if c in splitters and len(sentence) > 8 + 6:
                if pre_c in numbers:
                    continue
                self.sentences.append(sentence) # 加入句子列表
                sentence = ""
                
        if sentence:
            self.sentences.append(sentence)
        
        STATUS.SENTENCE_SUM = len(self.sentences)
        STATUS.set_COMMENTARY_SPEECH(self.sentences)
        
        if STATUS.TAKE_ACTION_EXPLAIN:
            # 发送讲稿时的起始动作（串行）
            self.request_service_and_send_actions(7, '*')
        
        # 依次播放句子
        while self.index_of_sentence < len(self.sentences):
            STATUS.SENTENCE_INDEX = 0
            for STATUS.SENTENCE_INDEX in range(self.index_of_sentence, len(self.sentences)):
                sentence_for_read = self.sentences[STATUS.SENTENCE_INDEX]
                
                if "〖Wait Util Someone Interrupt〗" in sentence_for_read:
                    self.WaitUtil = True
                    while True:
                        # 处理打断
                        interrupt_flag = self.listen_for_INT() # 监听打断信号
                        # print('if interrupt when 〖Wait Util Someone Interrupt〗', interrupt_flag)
                        if interrupt_flag:  # 打断后做出的处理
                            # TODO: 如果问答要做动作的话，就需要等待讲稿的动作结束！
                            sleep(0.1)  # 防止 self.handle_interrupt() 太快，在 text2speech 之前把 STATUS.is_interrupted 置为 False
                            return True

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
                print(f'合成完=“{sentence_for_read} ” 时间是=', datetime.now())

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
                print('if interrupt when Explaining', interrupt_flag)
                if interrupt_flag:  # 打断后做出的处理
                    # TODO: 如果问答要做动作的话，就需要等待讲稿的动作结束！
                    sleep(0.1)  # 防止 self.handle_interrupt() 太快，在 text2speech 之前把 STATUS.is_interrupted 置为 False
                    if_continue = self.handle_interrupt()  # 调用父类InterruptClass中的方法处理打断

                    if if_continue not in ['continue']: # 不是继续就直接结束讲解
                        STATUS.set_is_Explaining(False)
                        return False
                    
                    else: # 是继续就从上一句没说完的话开始讲
                        text2speech("下面继续讲解", index=0, is_beep=True)
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
                    
                    # 由于最后一个句子没有下一句，因此需要手动写打断处理来杀死最后一句
                    # 但是这样非常不优雅，因此最终改为使用在讲稿的最后一句后面加一个“？” 作为异步tts的下一句来杀死上一句
                    # while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
                    #     # 处理打断
                    #     interrupt_flag = self.listen_for_INT() # 监听打断信号
                    #     if interrupt_flag:  # 打断后做出的处理
                    #         # TODO: 如果问答要做动作的话，就需要等待讲稿的动作结束！
                    #         STATUS.Last_Play_Processor.kill()
                    #         break
                    
                    text2speech("？", index=1000)
                    
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
        if_card_set_success = self.set_master_index_by_keyword()
        if if_card_set_success:
            STATUS.set_card_id(-1)
        else:
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

        self.temp_last_area = '' # 上一个目标点只有在下一次导航开启的时候才会被更新

        rospy.init_node('interrupt', anonymous=False)

        # self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback) # 订阅ivw话题，唤醒词
        if STATUS.SOUND_INPUT_EXIST:
            self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback) # 订阅ivw话题，唤醒词

        if STATUS.FACE_DETECT:
            self.face_detect_queue = []
            self.face_detect_queue_size = 10
            self.face_detect_threshold = 0.2
            self.face_detect_flag = False
            self.face_sub = rospy.Subscriber("face_chatter", String, self.face_callback)  # 人脸检测
            
        if STATUS.FACE_RECOGNITION:
            self.face_recog_queue = []
            self.face_recog_queue_size = 10
            self.face_recog_threshold = 5
            self.face_recog_sub = rospy.Subscriber("face_recogniser", String, self.face_recog_callback)  # 人脸识别

        if STATUS.OBSTAC_STOP:
            self.obs_sub = rospy.Subscriber("obs_chatter", String, self.obs_callback)  # 深度停障
            self.yolo_sub = rospy.Subscriber("yolo_chatter", String, self.yolo_callback)  # 目标检测停障

        if STATUS.POSE_DETECT:
            self.pose_sub = rospy.Subscriber("pose_chatter", String, self.pose_callback)  # 手势识别
            
        if STATUS.HANDHELD_DETECT:
            self.handheld_sub = rospy.Subscriber("/mic_chatter", String, self.handheld_callback)  # 手持麦克风识别
            STATUS.set_Rotate_Publisher(rospy.Publisher('/cmd_vel', Twist, queue_size=1))  # 机器人转向
        
        if STATUS.LOW_COMPUTER_EXIST:
            STATUS.set_Navi_start_Subscriber(rospy.Subscriber("nav_state", String, self.navi_start_callback))  # 导航开始
            STATUS.set_Navi_end_Subscriber(rospy.Subscriber("nav_result", String, self.navi_end_callback))  # 导航结束
            STATUS.set_Navi_target_Publisher(rospy.Publisher("nav_target", String, queue_size=1))  # 导航目标点
            STATUS.set_Stop_Publisher(rospy.Publisher("stop_chatter", String, queue_size=1))  # 导航停止
            STATUS.set_Touchpad_Navi_Subscriber(rospy.Subscriber("touchpad_navi", String, self.touchpad_navi_callback))
            STATUS.set_Touchpad_Click_Publisher(rospy.Publisher("touchpad_chatter", String, queue_size=1))

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

    def set_master_index_by_keyword(self, keyword='pci-0000_00_1f'):
        # 运行 pactl list short sinks 命令
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error executing arecord -l")
            return None

        # 打印输出结果，方便调试
        # print(result.stdout)

        # 使用正则表达式来查找含有关键字的行，并提取卡片的索引号
        match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
        if match:
            masterid = int(match.group(1))
        else:
            return False
        # 同步执行的 run
        result = subprocess.run(['pactl', 'set-default-sink', str(masterid)], capture_output=True, text=True)
        return True

    def set_mic_index_by_keyword(self, keyword):
        # 运行 pactl list short sources 命令
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
            print(f"收到打断信号！现在可以打断", datetime.now())
            STATUS.set_is_Interrupted(True)
        else:
            # print(f"打断回调函数接收到打断信号，不可以打断")
            print(f"收到打断信号！现在不可以打断")

    def face_callback(self, data):
        # rospy.loginfo(rospy.get_caller_id() + "I heard %s from face", data.data)
        # print(f"人脸回调函数接收到人脸信号")
        """
        人脸位置消息格式：一帧一帧发
            [['LEFT','UP']] # 第一帧，表示镜头中所有人脸的平均位置是LEFT，UP
            ['NOBIGFACE'] # 第二帧，无大脸

        人名格式：
        [
            'songhao',
            'wangjizhe',
            'weimingjie',
            .........
        ]  # 这是一帧。
        """
        self.face_detect_flag = False
        face_position_of_frame = eval(data.data)
        # append之后的形式：类似于[[['LEFT','UP']],['NOBIGFACE'],......]
        self.face_detect_queue.append(face_position_of_frame)
        if len(self.face_detect_queue) >= self.face_detect_queue_size:
            self.face_detect_queue.pop(0)
        # print(self.face_detect_queue)
        r = self.face_detect_queue.count(["NOBIGFACE"])
        if r / len(self.face_detect_queue) <= self.face_detect_threshold:
            # print("ACTIVATE")
            self.face_detect_flag = True

        if face_position_of_frame == ["NOBIGFACE"]:
            STATUS.set_is_Big_Face_Detected(False)  # 没有检测到人脸
            STATUS.set_Big_Face_Area("NOBIGFACE")
        else:
            STATUS.set_is_Big_Face_Detected(True)  # 检测到人脸
            if face_position_of_frame[0][0] == "LEFT":
                STATUS.set_Big_Face_Area("LEFT")
            elif face_position_of_frame[0][0] == "RIGHT":
                STATUS.set_Big_Face_Area("RIGHT")
            else:
                STATUS.set_Big_Face_Area("CENTER")
            
    def face_recog_callback(self, data):
        # print(data.data)
        if data.data != "[]":
            face_name_list_from_string = ast.literal_eval(data.data)
            # print(face_name_list_from_string)
            face_name_list_by_dict = [STATUS.Face_Name_Dict[item] for item in face_name_list_from_string]
            # print(face_name_list_by_dict)
            # print(f"face_name_list_from_string: {face_name_list_from_string}")

            self.face_recog_queue.append(face_name_list_by_dict)
            if len(self.face_recog_queue) >= self.face_recog_queue_size:
                self.face_recog_queue.pop(0)
                
            # print(self.face_recog_queue)
        
    def obs_callback(self, data):
        if data.data == '++++':
            if STATUS.is_Depth_Obstacle == False:
                print(f"深度回调函数接收到障碍物信号")
            STATUS.set_is_Depth_Obstacle(True)
        else:
            STATUS.set_is_Depth_Obstacle(False)

    def yolo_callback(self, data):
        if data.data == '++++':
            if STATUS.is_Yolo_Obstacle == False:
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
        
    def handheld_callback(self, data):
        if 'has mic!!!' in data.data:
            if STATUS.HANDHELD_DETECT_FLAG == False:
                # print(f"手持麦克风回调函数接收到手持信号--{STATUS.COUNT_HANDHELD}")
                STATUS.set_COUNT_HANDHELD(STATUS.COUNT_HANDHELD+1)
        else:
            STATUS.set_COUNT_HANDHELD(0)
            STATUS.set_HANDHELD_DETECT_FLAG(False)
            
        if STATUS.COUNT_HANDHELD > 0:
            # print("找到手持麦克风的人")
            STATUS.set_HANDHELD_DETECT_FLAG(True)
        
    def navi_start_callback(self, data):
        STATUS.set_NAVI_START_FLAG(data.data)
        # print(data)
        # print(data.data)
        
    def navi_end_callback(self, data):
        STATUS.set_NAVI_END_FLAG(data.data)
        # print(data)
        # print(data.data)
        
    def touchpad_navi_callback(self, data):
        if STATUS.Touchpad_Area == 'NowIsInterrupted':
            print("触摸屏导航目标点:", data.data)
            STATUS.set_Touchpad_Area(data.data)
            STATUS.Touchpad_Click_Publisher.publish("TouchpadClick")
        else:
            print("非打断状态，忽略触摸屏点击")
            
    def find_next_destination(self, current_destination):
        # 试图解析当前destination的基本名称和数字后缀
        match = re.match(r"(.+?)(_\d+)?$", current_destination)
        if not match:
            raise(f"目标格式不正确{current_destination}")
        
        base_name = match.group(1)
        current_number = match.group(2)
        
        if current_number:
            # 提取当前后缀数字并计算下一个数字
            next_number = int(current_number.strip('_')) + 1
            next_destination = f"{base_name}_{next_number}"
        else:
            # 如果当前名称没有数字后缀，从1开始
            next_destination = f"{base_name}_1"
        
        # 检查生成的next_destination是否存在
        if next_destination in STATUS.Index_of_Vist:
            print(f"下一个展区是：{next_destination}，索引为：{STATUS.Index_of_Vist[next_destination]}")
            return True
        else:
            print("没有找到下一个展区。")
            return False

    # TODO: 让GPT4对文本进行切分并匹配动作（动作的执行时间应该与文本的播音时间匹配）尤其是说到数字时伸手指
    # TODO: 加上手势识别

    def settings(self):
        STATUS.set_ROBOT_NAME('K')
        
        # 设置所有功能开关
        STATUS.set_Enable_QA(True)              # 是否开启问答功能
        
        STATUS.set_TAKE_ACTION_QA(False)        # 问答时是否要做动作
        STATUS.set_TAKE_ACTION_EXPLAIN(False)   # 讲稿时是否要做动作
        STATUS.set_FACE_DETECT(False)           # 人脸检测
        STATUS.set_FACE_RECOGNITION(False)      # 人脸识别
        STATUS.set_OBSTAC_STOP(False)           # 停障
        STATUS.set_POSE_DETECT(False)           # 姿势检测
        STATUS.set_HANDHELD_DETECT(False)       # 手持麦克检测

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
        STATUS.set_DURATION(15)                  # 无人说话时每轮录音的时间
        STATUS.set_THRESHOLD_AUDIO(25)           # 超过该音量阈值识别到有人讲话

        # 在禁用OpenAI的情况下，会启用旧版问答程序
        if STATUS.MODEL_BAN_OPENAI:
            STATUS.set_MODEL_TASK_TYPE('chatglm')
            STATUS.set_MODEL_LLM_ANSWER('chatglm')

        STATUS.print_all_status()
    
    def welcome(self, ):
      
        # time.sleep(5)  
        
        # while False:  # 测试时跳过迎宾词，节约时间
        while True:
            print("进入welcome阶段")
            
            while True:
                # 人脸检测唤醒
                if STATUS.FACE_DETECT:
                    if STATUS.is_Big_Face_Detected:
                        break
                else:
                    break
    
            sleep(0.05)
            STATUS.set_is_Interrupted(False)
            
            # text2speech("各位游客大家好，请站在我面前[p50]或者说 “小红小红” 来唤醒我", index=0)
            # text2speech("各位游客大家好，请站在我面前来唤醒我", index=0)
            text2speech("各位游客大家好，我是小红" , index=0)
            text2speech("我可以带领大家按顺序参观展区", index=0)
            text2speech("您也可以让我带您去特定的展区，我还可以回答您关于展区的所有问题。", index=1000)
            STATUS.set_is_QAing(True)
            text2speech("请说 “小红小红” 来唤醒我", index=1000)
            STATUS.set_is_QAing(False)
            
            print("welcome唤醒提示音结束")
            
            sound_wake_up_count = 0
            while sound_wake_up_count < 800:
                # 语音唤醒
                if STATUS.SOUND_INPUT_EXIST:
                    if STATUS.is_Interrupted:
                        break
                sleep(0.01)
                sound_wake_up_count += 1
                
            if STATUS.SOUND_INPUT_EXIST:
                if STATUS.is_Interrupted:
                    sleep(0.05)
                    STATUS.set_is_Interrupted(False)
                    break
        
        sleep(0.05)
        STATUS.set_is_Interrupted(False)
        
        # 人脸识别迎宾语
        if STATUS.FACE_RECOGNITION:
            # 归零人名计数字典
            for key in STATUS.Recog_Count_Dict:
                STATUS.Recog_Count_Dict[key] = 0
                       
            # 遍历face_recog_queue中的所有人名列表，写入人名计数字典
            for name_list in self.face_recog_queue:
                for name in name_list:
                    if name in STATUS.Recog_Count_Dict:
                            STATUS.Recog_Count_Dict[name] += 1
                    else:
                        # 如果人名在STATUS.Recog_Count_Dict中不存在，可以选择忽略或做特殊处理
                        pass
                    
            popular_faces = [name for name, count in STATUS.Recog_Count_Dict.items() if count >= self.face_recog_threshold]
            
            def sort_func(name):
                return 0 if '老师' in name else 1

            popular_faces = sorted(popular_faces, key=sort_func)
            
            print(STATUS.Recog_Count_Dict)
            print(popular_faces)
            
            if len(popular_faces) > 0:
                face_name_join_str = '、'.join(popular_faces)
                if len(popular_faces) == 1:
                    hello_str = '你好'
                else:
                    hello_str = '你们好'
                STATUS.set_is_QAing(True)
                # print(f"{face_name_join_str}，{hello_str}！我是小红。")
                text2speech(f"{face_name_join_str}，{hello_str}！我是小红。", index=0)
                sleep(0.15)
                STATUS.set_is_QAing(False)
            else:
                text2speech(f"大家好！我是小红。", index=0)
        else:
            # text2speech(f"大家好！我是小红。", index=0)
            pass
        
        self.main()
        
    def main(self, ):
        # 先进行问答交互，直到游客要求参观整个展厅才开始主流程
        if_start = self.start.handle_interrupt()
        
        if if_start == 'start':
            print("开始完整参观流程")
            
        while True:
            current_destination = STATUS.Current_Order_of_Visit[0] if len(STATUS.Current_Order_of_Visit) > 0 else None # 获取下一个目标点
            current_destination_id = STATUS.get_first_Current_Order_of_Visit_id() # 获取下一个目标点的索引
            
            print_flag = False
            if current_destination_id != None: # 如果还有目标点，执行导航
                if print_flag:
                    print("\t\t\t\t\t\t\t\t\t\t\t\t44444 循环开始等待", datetime.now())
                # 如果上一动作没有执行完，就一直等待
                while not STATUS.EXPLAIN_SHOULD_ACTION:  # Ture就可以跳出循环继续做动作，False就需要一直等
                    if print_flag:
                        print("\t\t\t\t\t\t\t\t\t\t\t\t      正在做动作，等待")
                    continue
                if print_flag:
                    print("\t\t\t\t\t\t\t\t\t\t\t\t55555 等待完毕继续", datetime.now())

                # TODO: 按照 ExplainClass 类的逻辑处理引导词的打断
                
                # 只有主体目标点需要说好、好的
                if '_' not in current_destination:
                    # 好、好的
                    guodus = ['好', '好的']
                    a, b = 0, len(guodus)
                    choice = random.randint(a,b-1)
                    text = guodus[choice]
                    wavfile = f'/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/{text}.wav'
                    text2speech(text=text, index=0, wavfile=wavfile)
                        
                 # 过渡词：接下来带大家参观...
                transitional_sentence = STATUS.TRANSITIONAL_SENTENCE.get(current_destination, None)
                
                # 读过渡词
                if transitional_sentence:
                    print(f"获取到过渡词--目标点为 {current_destination}")
                    
                    text2speech(f"{transitional_sentence}", index=0)
                    # time.sleep(0.1)
                    
                    if STATUS.TAKE_ACTION_EXPLAIN:
                        transitional_action = STATUS.TRANSITIONAL_ACTION.get(current_destination, None)
                        if transitional_action:
                            # 过渡句的动作（串行）
                            self.explain_class.request_service_and_send_actions(
                                number=STATUS.ACTOIN_DICT.get(transitional_action),
                                index='*'
                                )
                else:
                    print(f"没有获取到过渡词--目标点为 {current_destination}")
                    
                print(f"\n执行去往 {current_destination} 目标点的导航\n")
                # print("wmjwmj, 刚刚开始导航", STATUS.Current_Order_of_Visit)

                if current_destination_id != 0:
                # if current_destination_id == -1:  # 关闭导航
                    if STATUS.TAKE_ACTION_EXPLAIN:
                        # 恢复直立状态（串行）
                        self.explain_class.request_service_and_send_actions(21, '*')
                    
                    # 只有 当前点非额外目标点 才能刷新上一个目标点
                    if '_' not in current_destination and current_destination != self.temp_last_area:
                        print(f"当前点 {current_destination}, 刷新上一个目标点")
                        STATUS.set_Last_Area(self.temp_last_area) # 下一次导航开始时，记录上一次导航的目标点

                    if_success_navigate = self.navigation_class.send_destination_and_handle_interrupt(current_destination_id) # 向下位机发送导航目标点

                    # print("interrupt_navigation正常跳出")
                    # print("\nif_success_navigate: ", if_success_navigate)

                else: 
                    if_success_navigate = True

                # 如果 1.导航成功 2.不是位于迎宾位置，则 执行讲解
                if if_success_navigate and current_destination_id != STATUS.Index_of_Vist.get('参观起始位置'):
                    # 修改当前位置
                    STATUS.set_Current_Area(STATUS.Current_Order_of_Visit[0])
                    print(f"设置当前区域为{STATUS.Current_Area}")
                    
                    # 只有 当前点非额外目标点 才能被记录
                    if '_' not in current_destination:
                        print(f"当前点 {current_destination}, 记录至上一个目标点")
                        self.temp_last_area = current_destination
                    
                    STATUS.Current_Order_of_Visit.pop(0)

                    print(f"\n执行位于 {current_destination} 目标点的讲解\n")
                    
                    # self.start.continue_rotate()

                    if_success_explain = self.explain_class.split_and_speech_text(current_destination) # 启动讲解
                    # print("\nif_success_explain: ", if_success_explain)
                    
                    # 如果 1.开启问答功能 2.讲解成功 3.后续没有额外导航点 则 执行问答
                    if STATUS.Enable_QA and if_success_explain and not self.find_next_destination(current_destination):
                        print(f"\n执行位于 {current_destination} 目标点的问答\n")

                        self.start.handle_interrupt()
                        
                elif current_destination_id == STATUS.Index_of_Vist.get('参观起始位置'):
                    STATUS.Current_Order_of_Visit.pop(0)
                
                # 重置flag值
                if_success_navigate = False
                if_success_explain = False                    

            else: # 如果没有目标点了，全流程结束
                break

        text2speech("参观到此结束，欢迎再来哈工大找我玩。", index=1000)
        print("任务结束")
    
if __name__ == "__main__":
    main_class = MainClass()
    
    # rostopic pub /nav_target std_msgs/String "data: '13'"