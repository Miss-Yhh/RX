import time
import rospy
from std_msgs.msg import String
from main.srv import msgCommand

import threading
import _thread as thread

import sys
sys.path.append('/home/kuavo/catkin_dt/src/voice_pkg/scripts')

# from voice_pkg.srv import VoiceSrv, VoiceSrvResponse
# from kedaxunfei_iat.iat_as_service import iat_web_api
from kedaxunfei_tts.tts_as_service import tts_playsound, tts_playsound_terminate
from tencentclound.tencentclound import iat_tencent as iat_web_api

from interrupt import get_ppl_bool
from interrupt import get_llm_rewrite
from interrupt import get_task_type
from interrupt import get_llm_answer
from interrupt import get_llm_check



def listenuser(text='ding'):
    userword = iat_web_api(text)
    # rospy.wait_for_service('kedaxunfei_iat')
    # try:
    #     iat_service = rospy.ServiceProxy('kedaxunfei_iat', VoiceSrv)
    #     res = iat_service(input=text, index=0)
    #     userword = res.output  # str ''
    # except rospy.ServiceException as e:
    #     print("Service call failed: %s"%e)
    #     userword = False
    return userword


class MainStream():
    def __init__(self) -> None:
        rospy.init_node('llm', anonymous=True)
        self.ivw_sub = rospy.Subscriber("ivw_chatter", String, self.ivw_callback)
        # self.iat_sub = rospy.Subscriber("iat_chatter", String, self.iat_callback)
        self.ifinterrupt = False
        self.userword = None
        self.sentindex = 0
        self.qaepoch = 3  # 最多等待3轮 3*15=45s
        self.speechindex = ['东方红展厅','火箭展厅','卫星展厅','院士展厅']

        self.now_speech_proc = None  # 记录现在说话音频的子线程
        self.now_speech_index = 0  # 记录现在说话音频是否异步

        self.qaclass_thread = threading.Thread(target=self.QAClassInit)
        self.qaclass_thread.start()

        self.arrival = False # 是否已经到达目标点停下

        self.strat_of_all()

    def QAClassInit(self):
        QaClass = get_llm_answer(model='gpt-4')
        self.qaclass = QaClass()
    
    def strat_of_all(self):
        # while True:
        #     if self.ifinterrupt:
        #         text2speech("我在。", index=0)
        #         text = self.pardon(pardon_round=2)
        #         if '参观' in text:
        #             text2speech("好的，我来带领大家参观航天馆。", index=1000)
        #             break
        self.ifinterrupt = False
        self.run()

    def run(self):
        allspeech = {
            '东方红展厅':'''“东方红，太阳升……”''',
            '火箭展厅':'''当中国的第一颗人造卫星东方红一号进入太空，中国从此走进了太空时代。 1970年4月24日东方红一号卫星搭载在长征一号运载火箭上从中国酒泉卫星发射中心成功发射。''',
            '火箭2号展厅':'''1965年5月6日，中央专委第十二次会议决定将人造卫星列入国家计划，代号六五一任务”。  这是东方红一号卫星模型， 其中一根天线为实物， 因当时共做了 5颗样星，第一颗卫星就发射成功，所以可以保存一根实物天线。东方红一号卫星由以钱学森为首任院长的中国空间技术研究院研制,两弹一星功勋科学家、 我校校友孙家栋院士，参与了东方红一号卫星的研制和发射工作。发射手胡世祥中将同为我校校友。 东方红一号卫星的成功发射使中国成为世界上继苏联、美国、法国和日本之后第五个完全依靠自己的力量成功发射人造卫星的国家。 ''',
            '卫星展厅':'''2016年3月8日，国务院批复将每年的 4月24日设立为中国航天日。  1999年9月18日，党中央、国务院、中央军委隆重表彰为我国“ 两弹一星 ”事业作出突出贡献的 23位科技专家， 这是我校校友运载火箭和卫星技术专家孙家栋院士。 接下来我们参观的是中国航天工程成就部分，着重展示了我国航天事业的代表性工程成就。 火箭是实现航天飞行的运载工具，其实质是一种无人驾驶的飞行器。它是目前唯一能使物体达到宇宙速度，克服或摆脱地球引力，进入宇宙空间的运载工具。人类经过无数执着的探索，研制出各种类型的火箭， 基本目的只有一个 ，那就是携带物体飞越空间。 我国运载火箭的研制起步于 20世纪60年代，搭载东方红一号人造卫星的就是长征一号火箭。 设计之初，大家想为火箭起一个合适的名字。中国运载火箭技术研究院第一总体设计部总体设计室的同志们，有感于毛主席著名的《七律·长征》中表 现出来的红军为实现革命目标，藐视一切困难、不惧任何艰难险阻的顽强斗志和勇往直前、不怕牺牲的大无畏精神，提出建议并经上级领导批准，将火箭命名为“长征”，寓意我国火箭事业一定会像红军长征一样，克服任何艰难险阻，到达胜利彼岸。“长征” 成为我国系列运载火箭的标志性名称， 一代代航天人也前赴后继，开启献身祖国航天事业的新长征。 在您的左手边的是运载火箭的舱段、整流罩和火箭燃料储箱，均为实物。 在您右手边的是中国研制的“长征系列”运载火箭家族模型。 “长征一号” 是我国第一种运载火箭型号， 1970年4月24日成功地将 “东方红一号”卫星送入预定轨道，奠定了“长征”系列火箭发展的基础。 “长征二号”火箭是目前中国最大的运载火箭家族，主要承担近地轨道和太阳同步轨道的发射任务，是中国航天运载器的基础型号。 “长征五号”运载火箭于 2016年11月3日在文昌航天发射场成功首飞，成为目前中国运载能力最强的火箭。 请随我继续参观人造地球卫星部分。''',
            '航天器展厅':'''人造地球卫星是环绕地球在空间轨道上运行的无人航天器，也是发射数量最多、用途最广、发展最快的航天器。自 1970年4月24日，成功发射第一颗人造卫星起，我国已形成 7个卫星系列。 分别是返回式遥感、科学技术试验、广播通信、气象、地球资源、导航定位、海洋 。这是“风云四号”气象卫星模型 风云四号是我国新一代静止轨道定量遥感气象卫星。我校参与完成多项技术攻关，如杂散辐射 传播和抑制 设计分析。 这是中国北斗导航卫星组网模型北斗卫星导航系统，简称北斗系统，是中国着眼于国家安全和经济社会发展需要，自主建设、独立运行的卫星导航系统，是为全球用户提供全天候、全天时、高精度的定位、导航和授时服务的国家重要空间基础设施。 展墙上着重展示了各系列卫星的代表型号，体现了我国在人造地球卫星领域的实力水平。 这是世界首颗量子科学实验卫星墨子号的模型。  这是“风云一号”气象卫星模型 风云一号是我国自主研制的第一代准极地太阳同步轨道气象卫星，共发射了4颗星。其中，风云一号 C星是中国首颗为世界所接纳的业务应用卫星。 ''',
            '运载火箭展厅':'''这是我国发射的第一颗返回式卫星“尖兵一号”的模型及其返回舱实物。1975年在太原卫星发射中心用长征二号运载火箭发射升空。自此，中国成为世界上第3个掌握卫星返回技术的国家。 '''
            # '火箭展厅':['这是第1个文本','这是第2个文本'],
            # '卫星展厅':['这是第1个文本','这是第2个文本'],
            # '院士展厅':['这是第1个文本','这是第2个文本'],
        }
        # text2speech('大家好！', index=1000)
        for locid, key in enumerate(self.speechindex):            
            # 调用导航服务，监听导航状态，如果到达一个目标点，self.arrival置True
            self.arrival = False

            text2speech("下面带大家参观"+key, index=0)
            thread.start_new_thread(self.navigate, (locid+1,))

            para = allspeech[key]
            splitters = [',', ';', '.','!','?',':', '，', '。', '！', "'", '；', '？', '：', '/']
            numbers = [str(c) for c in range(10)]
            # 切分段落为句子
            sent = ""
            pre_c = ''
            for c in (para):
                sent += c
                # 遍历字符，一旦碰到标点符号，就判断目前的长度
                if c in splitters and len(sent) > 8:
                    if pre_c in numbers:
                        continue

                    # 处理打断·
                    if self.ifinterrupt:
                        self.interrupt()
                        self.ifinterrupt = False
                    
                    # 发送文本到喇叭
                    text2speech(text=sent, index=0)  # 0就是异步播放
                    # self.sentindex = id
                    
                    sent = ""
                    if rospy.is_shutdown():
                        break
            if rospy.is_shutdown():
                break
            self.interrupt()

    def interrupt(self):
        # 直到机器人到达一个目标点停下，才进行问答环节
        # while self.arrival == False:
        #     continue
        # 说完一个讲稿，并且机器人已经到达一个目标点停下，进入问答的状态
        text2speech('大家有什么问题吗？', index=1000)

        userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
        if not userword:
            return

        msg = String(data=userword)
        action, text_rewrited = self.intent_recognition(msg)
        if 'qa' in action:
            # 只做问答
            self.multi_qa(text_rewrited)
            if self.ifinterrupt:
                textconfirm = text2speech("好的，那我继续讲解了", index=1000)
            else:
                textconfirm = text2speech("好的，那我带领大家参观下一个展厅", index=1000)
        elif 'sleep' in action:
            pass
        elif 'visit' in action:
            target_point = action.split(" ")[1]
            target_index = self.speechindex.index(target_point)
            print("\ntarget_index: ", target_index, "\n")
            self.navigate(location=target_index)
        else:
            # 继续
            if self.ifinterrupt:
                textconfirm = text2speech("好的，那我继续讲解了", index=1000)
            else:
                textconfirm = text2speech("好的，那我带领大家参观下一个展厅", index=1000)

    
    def text2speech(self, text, index):
        # 播放录音提示用户确认
        # textconfirm = tts_playsound(text, index)
        # return textconfirm
        if self.now_speech_index == 1000:
            self.now_speech_proc = tts_playsound_terminate(text, self.now_speech_index)
            self.now_speech_index = index
        return True
        # rospy.wait_for_service('kedaxunfei_tts')
        # try:
        #     tts_service = rospy.ServiceProxy('kedaxunfei_tts', VoiceSrv)
        #     res = tts_service(input=text, index=index)
        #     textconfirm = res.output  # str 'tts is over'
        # except rospy.ServiceException as e:
        #     print("Service call failed: %s"%e)
        #     textconfirm = False
     
    def ivw_callback(self, data):
        rospy.loginfo(rospy.get_caller_id() + "I heard %s from ivw", data.data)
        # 暂不处理打断
        self.ifinterrupt = True
        self.now_speech_proc.kill()
    
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
            textconfirm, index = text2speech_inter(text2tts, index=1000)
        else:
            # ppl小就是流畅

            # 以下注释掉的是大模型改写
            # text2tts = get_llm_rewrite(text)
            # totally_same = (text2tts == text) # 如果完全一致就不必确认了
            # 注释掉大模型改写之后的措施
            text2tts = text

            continue_flag = '有没有' not in text2tts and '没有' in text2tts
            if not continue_flag and not totally_same:
                text2speech('您想说的是不是:', index=1000)
                textconfirm = text2speech(text2tts, 1000)  # 1000是同步
            else:
                userword = text2tts
        # textconfirm = text2speech(text2tts, 1000)  # 1000是同步

        if textconfirm != 'tts is over':
            # 还需要处理喇叭出现问题的情况
            pass  

        if not continue_flag:
            # 使用iat录制用户的声音, 确认用户指令是否正确，最多重复ensure_round轮
            ensure_count = 0
            ensure_round = 2
            while ensure_count < ensure_round:
                if rospy.is_shutdown():
                    break
                ensure_count += 1

                if totally_same:
                    check_result = 'yes'
                else:
                    # 此处为了录制用户确认的语音，如果totally_same就不必确认
                    userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
                    if not userword:
                        break
                
                    check_result = get_llm_check(userword)

                totally_same = False

                if check_result == 'yes':
                    break
                elif check_result == 'no':
                    textconfirm = text2speech('请您重新说一遍您的问题', index=1000)
                    userword = self.pardon(pardon_round=2) # 反复录制直至用户语音不为空，最多重复pardon_round轮
                    if not userword:
                        break
                    check_result = get_llm_check(userword)
                    totally_same = (check_result == userword)

                    text2tts = check_result
                    continue_flag = '有没有' not in text2tts and '没有' in text2tts
                    if not continue_flag and not totally_same:
                        text2speech('您想说的是不是:', index=1000)
                        textconfirm = text2speech(text2tts, 1000)  # 1000是同步
                else:
                    text2tts = check_result
            
            if not userword:
                return None, None

        # 根据用户的话进行意图识别
        action = get_task_type(text2tts)  # str 
        '''
        1. qa
        2. sleep
        3. continue
        4. visit str(position)
        '''
        return action, text2tts

    def multi_qa(self, userword):
        text2speech("好的，请稍等，让我思索一下。", index=0)
        
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
            action, userword = self.intent_recognition(msg)
            if action == 'qa':
                text2speech("好的，请稍等，让我思索一下。", index=0)
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


    def navigate(self, location: int):
        # pub = rospy.Publisher('/nav_target', String, queue_size=10)
        # rospy.sleep(1)
        # msg = String()
        # msg.data = key
        # pub.publish(msg)
        # time.sleep(3)
        # wait for feedback
        try:
            leg_service = rospy.wait_for_service("command_msg")
            command_client = rospy.ServiceProxy("command_msg", msgCommand)
            response = command_client(location)
        except rospy.ROSException as e:
            rospy.loginfo("Timeout waiting for message.")
            self.arrival = False
        self.arrival = True
        
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
