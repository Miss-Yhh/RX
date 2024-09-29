import rospy
from std_msgs.msg import String
import sys
sys.path.append('/home/kuavo/catkin_dt/src')

# from voice_pkg.srv import VoiceSrv, VoiceSrvResponse
from kedaxunfei_tts.tts_as_service import tts_playsound
from kedaxunfei_iat.iat_as_service import iat_web_api
from interrupt import get_ppl_bool
from interrupt import get_llm_rewrite
from interrupt import get_task_type
from interrupt import get_llm_answer

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
        self.run()

    def run(self):
        allspeech = {
            # '火箭展厅':['这是第1个文本','这是第2个文本','这是第3个文本','这是第4个文本','这是第5个文本'],
            # '卫星展厅':['这是第1个文本','这是第2个文本','这是第3个文本','这是第4个文本','这是第5个文本'],
            # '院士展厅':['这是第1个文本','这是第2个文本','这是第3个文本','这是第4个文本','这是第5个文本'],

            '火箭展厅':['这是第1个文本','这是第2个文本'],
            '卫星展厅':['这是第1个文本','这是第2个文本'],
            '院士展厅':['这是第1个文本','这是第2个文本'],
        }
        text2speech('大家好！', index=1000)
        for key in self.speechindex:
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
            # 说完一个讲稿了，进入问答的状态
            text2speech('大家有什么问题吗？', index=1000)
            userword = listenuser('ding')
            msg = String(data=userword)
            action = self.intent_recognition(msg)  
            print('---------action == ', action)  
            if 'qa' in action:
                # 只做问答
                self.multi_qa(userword)
                
            elif 'sleep' in action:
                # 睡眠先不做
                self.speechindex = 0
            else:
                # 继续
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
            textconfirm = text2speech(f'您想说的是:{text2tts}吗？', index=1000)
        # textconfirm = text2speech(text2tts, 1000)  # 1000是同步

        if textconfirm != 'tts is over':
            # 还需要处理喇叭出现问题的情况
            pass  

        # 使用iat录制用户的声音
        userword = listenuser('ding')  # userword = 不是的，不是的

        pardon_count = 0
        while not userword and pardon_count < 2:
            pardon_count += 1
            text2speech('不好意思我没有听清，请您重说一遍', index=0)
            userword = listenuser('ding')
        
        # yesornot = get_llm_check(userword)

        # if yesornot == False:
        #     text2speech('您想说的是:', index=0)
        #     textconfirm = text2speech(text2tts, 1000)  # 1000是同步

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
        QaClass = get_llm_answer(model='gpt-4')
        qaclass = QaClass()
        action = 'qa'
        for i in range(self.qaepoch):
            if action == 'qa':
                qa_answer = qaclass.process_query(userword)
            text2speech(qa_answer, index=0)
            text2speech('好的，我说完了，大家还有什么问题吗？', index=1000)
            userword = listenuser('ding')
            action = self.intent_recognition(userword)
            if action == 'continue':
                break

    def pardon(self, pardon_thres):
        # 反复录制用户语音，直至语音不为空或达到次数上限
        userword = listenuser('ding')

        pardon_count = 0
        while not userword and pardon_count < pardon_thres:
            pardon_count += 1
            text2speech('不好意思我没有听清，请您重说一遍', index=0)
            userword = listenuser('ding')
        return userword

from datetime import datetime
if __name__ == '__main__':
    # mainstream = MainStream()
    # mainstream.run()
    time1 = datetime.now()
    userword = '请问风云4号是什么？'
    DocumentQAgpt = get_llm_answer('huozi')
    doc_qa_class = DocumentQAgpt()
    answer = doc_qa_class.process_query(userword)
    print(answer)
    time12= datetime.now()
    print(f'time cost= {time12 - time1}')
