import rospy
from std_msgs.msg import String

import threading

import sys
sys.path.append('/home/kuavo/catkin_dt/src')

# from voice_pkg.srv import VoiceSrv, VoiceSrvResponse
from kedaxunfei_tts.tts_as_service import tts_playsound
from kedaxunfei_iat.iat_as_service import iat_web_api

from interrupt import get_ppl_bool
from interrupt import get_llm_rewrite
from interrupt import get_task_type
from interrupt import get_llm_answer
from interrupt import get_llm_check

def text2speech(text, index):
    # 播放录音提示用户确认
    textconfirm = tts_playsound(text, index)
    # rospy.wait_for_service('kedaxunfei_tts')
    # try:
    #     tts_service = rospy.ServiceProxy('kedaxunfei_tts', VoiceSrv)
    #     res = tts_service(input=text, index=index)
    #     textconfirm = res.output  # str 'tts is over'
    # except rospy.ServiceException as e:
    #     print("Service call failed: %s"%e)
    #     textconfirm = False
    return textconfirm

def listenuser(text='ding'):
    # rospy.wait_for_service('kedaxunfei_iat')
    # try:
    #     iat_service = rospy.ServiceProxy('kedaxunfei_iat', VoiceSrv)
    #     res = iat_service(input=text, index=0)
    #     userword = res.output  # str ''
    # except rospy.ServiceException as e:
    #     print("Service call failed: %s"%e)
    #     userword = False
    userword = iat_web_api(text)
    return userword


class MainStream():
    def __init__(self) -> None:
        rospy.init_node('llm', anonymous=True)
        # self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback)
        # self.iat_sub = rospy.Subscriber("iat_chatter", String, self.iat_callback)
        self.ifinterrupt = False
        self.userword = None
        self.sentindex = 0
        self.qaepoch = 3  # 最多等待3轮 3*15=45s
        self.speechindex = ['火箭展厅','卫星展厅','院士展厅']

        self.qaclass_thread = threading.Thread(target=self.QAClassInit)
        self.qaclass_thread.start()

        self.arrival = False # 是否已经到达目标点停下

        self.run()

    def QAClassInit(self):
        QaClass = get_llm_answer(model='gpt-4')
        self.qaclass = QaClass()
    
    def run(self):
        allspeech = {
            # '火箭展厅':['这是第1个文本','这是第2个文本','这是第3个文本','这是第4个文本','这是第5个文本'],
            # '卫星展厅':['这是第1个文本','这是第2个文本','这是第3个文本','这是第4个文本','这是第5个文本'],
            # '院士展厅':['这是第1个文本','这是第2个文本','这是第3个文本','这是第4个文本','这是第5个文本'],

            '火箭展厅':['这是第1个文本','这是第2个文本'],
            '卫星展厅':['这是第1个文本','这是第2个文本'],
            '院士展厅':['这是第1个文本','这是第2个文本'],
        }

        # 开始的时候需要用唤醒词唤醒，用户下指令“参观”
        while True:
            userword = self.pardon(pardon_round=2)
            if '参观' in userword:
                text2speech("好的，下面带您参观航天馆。", index=0)
                break

        # text2speech('大家好！', index=1000)
        for key in self.speechindex:
            # 调用导航服务，监听导航状态，如果到达一个目标点，self.arrival置True

            for id, sent in enumerate(allspeech[key]):
                text2speech(text=sent, index=0)  # 0就是异步播放
                self.sentindex = id

                # 暂时不处理打断
                # if self.ifinterrupt:
                #     return
                if rospy.is_shutdown():
                    break
            if rospy.is_shutdown():
                break

            # 直到机器人到达一个目标点停下，才进行问答环节

            # 说完一个讲稿，并且机器人已经到达一个目标点停下，进入问答的状态
            text2speech('大家有什么问题吗？', index=1000)

            userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
            if not userword:
                continue

            msg = String(data=userword)
            action = self.intent_recognition(msg)
            if 'qa' in action:
                # 只做问答
                self.multi_qa(userword)
                
            elif 'sleep' in action:
                # 睡眠先不做
                self.speechindex = 0
            else:
                # 继续
                textconfirm = text2speech("好的，那我带领大家参观下一个展厅", index=1000)
                continue
            if rospy.is_shutdown():
                break

    def ivw_callback(self, data):
        rospy.loginfo(rospy.get_caller_id() + "I heard %s from ivw", data.data)
        # 暂不处理打断
        # self.ifinterrupt = True
    
    def iat_callback(self, data):
        rospy.loginfo(rospy.get_caller_id() + "I heard %s from iat", data.data)
        text = data.data
        self.userword = text

    def intent_recognition(self, data):
        text = data.data

        continue_flag = False
        textconfirm = 'tts is over'

        # 打断并录音之后返回的文本，给到ppl
        ppl_bool = get_ppl_bool(text)
        text2tts = None
        if ppl_bool == False:
            # ppl太大了
            text2tts = '不好意思没听懂你说的啥'
            textconfirm = text2speech(text2tts, index=1000)
        else:
            # ppl小就是流畅
            text2tts = get_llm_rewrite(text)

            continue_flag = '有没有' not in text2tts and '没有' in text2tts
            if not continue_flag:
                text2speech('您想说的是不是:', index=0)
                textconfirm = text2speech(text2tts, 1000)  # 1000是同步
        # textconfirm = text2speech(text2tts, 1000)  # 1000是同步

        if textconfirm != 'tts is over':
            # 还需要处理喇叭出现问题的情况
            pass  

        if not continue_flag:
            # 使用iat录制用户的声音, 确认用户指令是否正确，最多重复ensure_round轮
            ensure_count = 0
            ensure_round = 2
            while ensure_count < ensure_round:
                ensure_count += 1

                userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
                if not userword:
                    break
                
                check_result = get_llm_check(userword)

                if check_result == 'yes':
                    break
                elif check_result == 'no':
                    textconfirm = text2speech('请您重新说一遍您的问题', index=1000)
                    userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
                    if not userword:
                        break
                    text2tts = userword
                    continue_flag = '有没有' not in text2tts and '没有' in text2tts
                    if not continue_flag:
                        text2speech('您想说的是不是:', index=1000)
                        textconfirm = text2speech(text2tts, 1000)  # 1000是同步
                else:
                    text2tts = check_result
            
            if not userword:
                return None

        # 根据用户的话进行意图识别
        action = get_task_type(text2tts)  # str 
        '''
        1. qa
        2. sleep
        3. continue
        4. visit str(position)
        '''
        return action

    def multi_qa(self, userword):
        text2speech("请稍等，让我思索一下。", index=0)
        
        # 文档检索问答模型初始化完成
        self.qaclass_thread.join()

        action = 'qa'
        for i in range(self.qaepoch):
            time_before_llm_answer = datetime.now()
            if action == 'qa':
                qa_answer = self.qaclass.process_query(userword)
            time_after_llm_answer = datetime.now()
            print("\n大模型耗时:", time_after_llm_answer - time_before_llm_answer, "\n")
            text2speech(qa_answer, index=1000)
            text2speech('我说完了，大家还有问题吗？', index=1000)
            userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
            msg = String(data=userword)
            action = self.intent_recognition(msg)
            if action == 'continue':
                break

    def pardon(self, pardon_round):
        # 反复录制用户语音，直至语音不为空，最多重复pardon_round轮
        userword = listenuser('ding')

        pardon_count = 0
        while not userword and pardon_count < pardon_round:
            pardon_count += 1
            text2speech('不好意思我没有听清，请您重说一遍', index=1000)
            userword = listenuser('ding')
        return userword

from datetime import datetime
if __name__ == '__main__':
    mainstream = MainStream()
    mainstream.run()
    # time1 = datetime.now()
    # userword = '请问风云4号是什么？'
    # DocumentQAgpt = get_llm_answer('huozi')
    # doc_qa_class = DocumentQAgpt()
    # answer = doc_qa_class.process_query(userword)
    # print(answer)
    # time12= datetime.now()
    # print(f'time cost= {time12 - time1}')
