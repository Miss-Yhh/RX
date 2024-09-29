# ===============
# Author: hsong
# Quote: 先不用property封装
# ===============


from typing import Dict, List, Tuple, Optional
import inspect
import yaml, os
from copy import deepcopy

from std_msgs.msg import String
try:
    from harbin_pkg.msg import stopProcessing
except:
    pass
    # print("failed to import ..")
class GlobalValuesClass:
    """
    Class Description: 用于管理全局数值的类。

    Attributes:
        _id (int): 类属性，用于记录实例的唯一标识符。
        _all_instances (dict): 类属性，用于存储所有实例的字典，键为实例ID，值为实例对象。
        
    到达一个地方，需要维护：
        STATUS.set_Current_Area(new_Current_Area)
        ...
    """

    _id = 0 
    _all_instances = {}  

    def __init__(
            self, 
            
            ROBOT_NAME:str='',                               # 机器人名称 
            
            Enable_QA:bool=False,                           # 是否开启问答功能
            TAKE_ACTION_QA:bool=False,                      # 问答时是否要做动作
            TAKE_ACTION_EXPLAIN:bool=False,                 # 讲稿时是否要做动作
            FACE_DETECT:bool=False,                         # 是否开启人脸检测功能
            FACE_RECOGNITION:bool=False,                    # 是否开启人脸识别功能
            OBSTAC_STOP:bool=False,                         # 是否开启停障功能
            POSE_DETECT:bool=False,                         # 是否开启姿势检测功能
            HANDHELD_DETECT:bool=False,                     # 是否开启手持麦克风检测功能
            ARM_ACTION:bool=False,                          # 是否开启手部动作功能
            POSE_DETECT_KEYWORD:str='',                     # 姿势检测到的物品关键词
            HANDHELD_DETECT_FLAG:bool=False,                # 手持麦克风检测标志
            Action_from_User:str="None",                    # 问答时用户指定的动作
            EXPLAIN_SHOULD_ACTION:bool=True,                # 讲稿过程中，是否应该做动作

            COMMENTARY_SPEECH:str='',                       # 目前处于的展区所对应的讲稿
            SENTENCE_SUM:int=0,                             # 讲稿需要读的句子总数
            SENTENCE_INDEX:int=0,                           # 讲稿现在读到的句子序号
            LAST_BROAD_WORDS:str="",                        # 打断之前最后播音的话，用于日志记录

            COUNT_OBS:int=0,                                # depth障碍缓存
            COUNT_YOLO:int=0,                               # yolo障碍缓存
            COUNT_FACE:int=0,                               # 人脸检测缓存
            COUNT_POSE:int=0,                               # 手势识别缓存
            COUNT_HANDHELD:int=0,                           # 手持麦克风识别缓存

            MODEL_TASK_TYPE:str="",                         # 用于做任务分类的模型
            MODEL_LLM_ANSWER:str="",                        # 用于回答问题的模型
            MODEL_BAN_OPENAI:bool=False,                    # 是否禁用OpenAI
            STREAM_RETURN:bool=False,                       # 是否使用流式返回

            LOW_COMPUTER_EXIST:bool=False,                  # 下位机是否存在
            SOUND_INPUT_EXIST:bool=True,                    # 录音设备是否存在
            SOUND_OUTPUT_EXIST:bool=True,                   # 播音设备是否存在
            
            NAVI_START_FLAG:bool=False,                     # 导航是否开始
            NAVI_END_FLAG:bool=False,                       # 导航是否结束

            DURATION:int=2,                                 # 无人说话时每轮录音的时间
            THRESHOLD_AUDIO=8,                              # 超过该音量阈值识别到有人讲话
            SOUND_CHANGE=5,                                 # 合成播音时的音量增减值
            
            info: Optional[str] = None,                     # 当前实例的描述信息，随意
            name:str="This is a glabolvalues",              # 当前实例的描述信息，随意
            is_Navigating:bool=False,                       # robot是否处于移动状态
            is_Depth_Obstacle=False,                        # robot是否从深度信息检测到障碍物
            is_Yolo_Obstacle=False,                         # robot是否从yolo信息检测到障碍物
            is_Explaining:bool=False,                       # robot是否处于讲解状态
            is_QAing:bool=False,                            # robot是否处于QA状态
            is_Interrupted:bool=False,                      # robot是否处于被打断的状态
            is_Big_Face_Detected:bool=False,                # robot是否检测到人脸
            Big_Face_Area:str = "LEFT",                     # robot检测到的人脸区域
            Face_Name_Dict:dict =                           # 人脸姓名字典
            {
                'liuting': '刘挺老师',
                'zhangweinan': '张伟男老师',
                'zhaolijun': '赵立军老师',
                'wangjizhe': '王寄哲同学',
                'weimingjie': '韦明杰同学',
                'songhao': '宋浩同学',
                'NOFACE': '无人',
                'UNKNOWNPERSON': '不认识',
            },
            Recog_Count_Dict:dict = {},                     # 键是人名，值是出现的次数
            
            Block_Navigation_Thread:bool=False,             # 是否阻止导航进程返回
            Current_Area:str="",                            # robot当前area
            Last_Area:str="",                               # robot上一个area
            Destination_Area:str="",                        # Navigate目标area
            Touchpad_Area:str="",                           # 触摸屏给出的目标area
            Current_Position:Optional[List[float]]=None,    # robot当前精确坐标，可不写       
            Target_Position:Optional[List[float]]=None,     # robot目标精确坐标，可不写
            is_Arrived:bool=False,                          # robot到达指定地点，
            
            Index_of_Document:int = 0,                      # 讲解被打断时 记录的文稿索引位置
            Last_Sentence:str = "",                         # 讲解被打断时 记录的最近一句话
            
            Interrupt_Area:Optional[str]=None,              # 移动被打断时 记录当时所处的展厅区域
            Interrupt_Position:Optional[List[float]]=None,  # 移动被打断时 记录当时所处的精确坐标

            Navi_start_Subscriber:Optional[object]=None,    # 导航开始          接收者
            Navi_end_Subscriber:Optional[object]=None,      # 导航结束          接收者
            Navi_target_Publisher:Optional[object]=None,    # 导航目标点        发布者
            Stop_Publisher:Optional[object]=None,           # 终止导航          发布者
            Rotate_Publisher:Optional[object]=None,         # 转向              发布者
            Touchpad_Navi_Subscriber:Optional[object]=None, # 触控板导航目标点   接收者
            Touchpad_Click_Publisher:Optional[object]=None, # 触控板点击事件     发布者
            
            Arm_Action_Publisher:Optional[String]=None,     # 手臂动作发布者
            card_id:int=0,                                  # 声卡id
            
            SCAN_DIRECTION = 'LEFT',                        # 当前扫视的方向
            HEAD_ANGLE = '-15',                             # 机器人当前头的角度
            
            # 'X' 相关信息
            Abb_of_Visit_X:Dict={
                "服务":"服务及医疗机器人展区", 
                "宇航":"宇航空间机构及控制展区", 
                "工业":"工业及特种机器人展区",
                "空间":"空间机器人展区", 
                "机器人":"机器人基础功能部件展区", 
                "微纳":"微纳及仿生机器人展区", 
                "概况":"实验室概况展区",
                "队伍":"实验室队伍展区", 
                "大屏幕":"实验室宣传视频展区", 
                "展望":"未来展望展区", 
                "开放服务":"开放服务展区", 
                "关怀":"领导关怀及荣誉展区",
                },
            Index_of_Vist_X:Dict={                       # 记录展区索引
                "初始位置":0, 
                "参观起始位置":1,
                "实验室宣传视频展区":2, 
                "实验室概况展区":3,
                "实验室概况展区_1":4,
                "微纳及仿生机器人展区":5, 
                "微纳及仿生机器人展区_1":6, 
                "微纳及仿生机器人展区_2":7,
                "空间机器人展区":8, 
                "空间机器人展区_1":9,
                "空间机器人展区_2":10,
                "宇航空间机构及控制展区":11, 
                "宇航空间机构及控制展区_1":12,
                "服务及医疗机器人展区":13,
                "服务及医疗机器人展区_1":14,
                "服务及医疗机器人展区_2":15,
                "工业及特种机器人展区":16,
                "工业及特种机器人展区_1":17,
                "工业及特种机器人展区_2":18,
                "工业及特种机器人展区_3":19,
                "机器人基础功能部件展区":20,
                "实验室队伍展区":21,
                "领导关怀及荣誉展区":22,
                "领导关怀及荣誉展区_1":23,
                "领导关怀及荣誉展区_2":24,
                "开放服务展区":25,
                "未来展望展区":26,
                },
            Origin_Order_of_Visit_X:List[str]=[               # robot默认原始参观顺序列表  
                "实验室宣传视频展区",
                "实验室概况展区",
                "实验室概况展区_1",
                "微纳及仿生机器人展区",
                "微纳及仿生机器人展区_1",
                "微纳及仿生机器人展区_2",
                "空间机器人展区",
                "空间机器人展区_1",
                "空间机器人展区_2",
                "宇航空间机构及控制展区",
                "宇航空间机构及控制展区_1",
                "服务及医疗机器人展区",
                "服务及医疗机器人展区_1",
                "服务及医疗机器人展区_2",
                "工业及特种机器人展区",
                "工业及特种机器人展区_1",
                "工业及特种机器人展区_2",
                "工业及特种机器人展区_3",
                "机器人基础功能部件展区",
                "实验室队伍展区",
                "领导关怀及荣誉展区",
                "领导关怀及荣誉展区_2",
                "参观起始位置",
                ],
            Current_Order_of_Visit_X:List[str]=[              # robot当前任务列表，完成一个就pop一个
                "实验室宣传视频展区",
                "实验室概况展区",
                "实验室概况展区_1",
                "微纳及仿生机器人展区",
                "微纳及仿生机器人展区_1",
                "微纳及仿生机器人展区_2",
                "空间机器人展区",
                "空间机器人展区_1",
                "空间机器人展区_2",
                "宇航空间机构及控制展区",
                "宇航空间机构及控制展区_1",
                "服务及医疗机器人展区",
                "服务及医疗机器人展区_1",
                "服务及医疗机器人展区_2",
                "工业及特种机器人展区",
                "工业及特种机器人展区_1",
                "工业及特种机器人展区_2",
                "工业及特种机器人展区_3",
                "机器人基础功能部件展区",
                "实验室队伍展区",
                "领导关怀及荣誉展区",
                "领导关怀及荣誉展区_2",
                "参观起始位置",
                ],
            Trun_Direction_X:Dict={                      # robot在每个参观点的转向方向
                "初始位置":"middle", 
                "参观起始位置":"middle",
                "实验室宣传视频展区":"middle", 
                "实验室概况展区":"right",
                "实验室概况展区_1":"right",
                "微纳及仿生机器人展区":"right", 
                "微纳及仿生机器人展区_1":"right", 
                "微纳及仿生机器人展区_2":"middle",
                "空间机器人展区":"right", 
                "空间机器人展区_1":"right",
                "空间机器人展区_2":"middle",
                "宇航空间机构及控制展区":"right", 
                "宇航空间机构及控制展区_1":"right",
                "服务及医疗机器人展区":"left",
                "服务及医疗机器人展区_1":"right",
                "服务及医疗机器人展区_2":"left",
                "工业及特种机器人展区":"left",
                "工业及特种机器人展区_1":"middle",
                "工业及特种机器人展区_2":"middle",
                "工业及特种机器人展区_3":"middle",
                "机器人基础功能部件展区":"right",
                "实验室队伍展区":"middle",
                "领导关怀及荣誉展区":"left",
                "领导关怀及荣誉展区_1":"left",
                "领导关怀及荣誉展区_2":"middle",
                "开放服务展区":"middle",
                "未来展望展区":"middle",
                },
            EXTRA_INFORMATION_X:Dict={
                "初始位置":"这是机器人启动时的初始点位", 
                "参观起始位置":"这是机器人迎接游客的起始位置，机器人在这里等待游客",
                "实验室宣传视频展区":"机器人的右后方有一块大屏幕，这块大屏幕会播放实验室的宣传视频", 
                "实验室概况展区":"机器人后方的展板上介绍了实验室概况",
                "实验室概况展区_1":"机器人后方的展板上介绍了实验室定位、实验室特色、实验室研究方向",
                "微纳及仿生机器人展区":"机器人左后方的展板上介绍了微纳机器人，包括微纳游动机器人、维纳操作机器人", 
                "微纳及仿生机器人展区_1":"机器人左后方的展板上介绍了仿生机器人，包括水黾机器人、四足机器人、六足机器人、仿生青蛙、扑翼飞行机器人、模块化自重重构机器人", 
                "微纳及仿生机器人展区_2":"机器人的右方有两个扑翼飞行机器人实物，是两只仿生凤凰",
                "空间机器人展区":"机器人的左前方有空间机械臂实物，机器人的左后方有空间灵巧手实物，机器人后方的展板上介绍了空间灵巧手、空间机械臂", 
                "空间机器人展区_1":"机器人的左前方有空间机械臂实物，机器人的左后方有空间灵巧手实物，机器人后方的展板上介绍了空间灵巧手、空间机械臂",
                "空间机器人展区_2":"机器人的左前方有空间机械臂实物，机器人的左后方有空间灵巧手实物，机器人后方的展板上介绍了空间灵巧手、空间机械臂",
                "宇航空间机构及控制展区":"机器人的左前方有星球探索机器人实物机器人后方的展板上介绍了星表移动与探测技术、空间折展机构与变形翼技术、操控作业与采样技术、空间先进连接与分离技术", 
                "宇航空间机构及控制展区_1":"机器人的左前方星球探索机器人实物，机器人后方的展板上介绍了星表移动与探测技术、空间折展机构与变形翼技术、操控作业与采样技术、空间先进连接与分离技术",
                "服务及医疗机器人展区":"机器人的右边有微创腹腔镜手术机器人实物",
                "服务及医疗机器人展区_1":"机器人左后方的展板上介绍了服务机器人，包括高铁底部巡检机器人，档案机器人，智能服务机器人，电网服务机器人、助老助残机器人、银行专业服务机器人、穿戴式辅助增强机器人，机器人右后方的展板上介绍了医疗机器人，包括康复机器人、智能假肢、眼科显微手术机器人、多孔腔镜，机器人右边有穿戴式辅助增强机器人（外骨骼机器人）实物",
                "服务及医疗机器人展区_2":"机器人左后方的展板上介绍了服务机器人，包括高铁底部巡检机器人，档案机器人，智能服务机器人，电网服务机器人、助老助残机器人、银行专业服务机器人、穿戴式辅助增强机器人，机器人右后方的展板上介绍了医疗机器人，包括康复机器人、智能假肢、眼科显微手术机器人、多孔腔镜，机器人右边有穿戴式辅助增强机器人（外骨骼机器人）实物",
                "工业及特种机器人展区":"机器人的右边有弧焊机器人实物，机器人右边的展板上介绍了工业机器人，包括电石出炉机器人、焊接机器人、协作型工业机器人、码垛机器人、喷涂机器人",
                "工业及特种机器人展区_1":"机器人的左边有人机协作型工业机器人实物，机器人左后方的展板上介绍了工业机器人，包括电石出炉机器人、焊接机器人、协作型工业机器人、码垛机器人、喷涂机器人",
                "工业及特种机器人展区_2":"机器人的左边有履带式排爆机器人实物，机器人左后方的展板上介绍了特种机器人，包括救援机器人、特种测试装备、国防军用机器人、特种环境机器人",
                "工业及特种机器人展区_3":"机器人的左边有负压吸附式爬壁机器人实物，机器人左后方的展板上介绍了特种机器人，包括救援机器人、特种测试装备、国防军用机器人、特种环境机器人",
                "机器人基础功能部件展区":"机器人左边的展柜上摆放着高温关节轴承、深海电机、深地测井电机、无框架电机、复合模态压电换能器、内嵌陶瓷型行波压电超声驱动器、超低温高速精密陶瓷轴承、鼠笼弹支一体化轴承、带挤压油膜阻尼器的异形结构航空轴承、微弧度级二维驱动器/指向器、伺服驱动器等实物",
                "实验室队伍展区":"机器人的右边有“实验室队伍”展板，上面包含四位两院院士（蔡鹤皋、邓宗全、段广仁、刘宏）的照片、空间机器人团队各位老师的照片、宇航空间机构及控制团队各位老师的照片、工业及特种机器人研究团队各位老师的照片、服务及医疗机器人研究团队各位老师的照片、微纳及仿生机器人研究团队各位老师的照片、基础交叉研究团队各位老师的照片",
                "领导关怀及荣誉展区":"机器人右边的展板上展示了实验室获得的各种国家级奖项，以及习近平总书记等国家领导来实验室视察的照片",
                "领导关怀及荣誉展区_1":"机器人右边的展板上展示了实验室获得的各种国家级奖项，以及习近平总书记等国家领导来实验室视察的照片",
                "领导关怀及荣誉展区_2":"机器人左后方的展板上展示了实验室获得的各种国家级奖项，以及习近平总书记等国家领导来实验室视察的照片",
                "开放服务展区":"机器人后面的展板上介绍了实验室的科学传播活动以及学术交流与合作活动",
                "未来展望展区":"机器人后面的大屏幕上播放着有关实验室未来展望的视频",
                },
            TRANSITIONAL_SENTENCE_X:Dict={               # 对应于每一个讲解点的过渡句
                "实验室概况展区":"接下来，请大家随我一起参观实验室概况展区",
                "实验室概况展区_1":"下面介绍实验室的研究方向",
                "微纳及仿生机器人展区":"接下来我分方向为大家介绍一下，我们的机器人", 
                "微纳及仿生机器人展区_1":"下一个是仿生机器人方向", 
                "微纳及仿生机器人展区_2":"下一个是仿生机器人方向", 
                "空间机器人展区":"下一个方向，是刘宏院士团队在做的空间机器人",
                "空间机器人展区_1":"下一个展品是天空二号的机械臂", 
                "空间机器人展区_2":"接下来给大家介绍一下机械臂上的灵巧手", 
                "宇航空间机构及控制展区":"接下来，请大家随我一起参观宇航空间机构及控制展区", 
                "宇航空间机构及控制展区_1":"下一个方向是空间折展机构", 
                "服务及医疗机器人展区":"下一个方向是服务和医疗机器人", 
                "服务及医疗机器人展区_1":"下面介绍高铁底部巡检机器人", 
                "服务及医疗机器人展区_2":"下一个比较有代表性的是外骨骼机器人", 
                "工业及特种机器人展区":"下一个方向是工业机器人",
                "工业及特种机器人展区_1":"再介绍一下码垛机器人和电石出炉机器人",
                "工业及特种机器人展区_2":"下面是特种环境机器人",
                "机器人基础功能部件展区":"接下来，请大家随我一起参观机器人基础功能部件展区", 
                "实验室队伍展区":"接下来，请大家随我一起参观实验室队伍展区", 
                "实验室宣传视频展区":"接下来，请大家随我一起参观实验室宣传视频展区", 
                "未来展望展区":"接下来，请大家随我一起参观未来展望展区", 
                "参观开放服务展区":"接下来，请大家随我一起参观开放服务展区", 
                "领导关怀及荣誉展区":"接下来，请大家随我一起参观领导关怀及荣誉展区",
                "领导关怀及荣誉展区_2":"还有我们获得的一些国家技术发明奖的证书。[p2000]接下来是我们团队，还有我们学生比赛获得的一些荣誉",
                "参观起始位置":"下面我要回到初始位置啦",
                },
            ACTOIN_DICT_X={                                   # 所有的动作及其索引
                
                },
            TRANSITIONAL_ACTION_X:Dict={                 # 对应于每一个讲解点的过渡句的动作
                
                },
            
            # 'K' 相关信息
            Abb_of_Visit_K:Dict={
                
                },
            Index_of_Vist_K:Dict={                       # 记录展区索引
                "东方红一号卫星展区":0, 
                "中国航天工程成就展区":1,
                "人造地球卫星展区":2, 
                "七大系列卫星展区":3,
                },
            Origin_Order_of_Visit_K:List[str]=[               # robot默认原始参观顺序列表  
                "东方红一号卫星展区", 
                "中国航天工程成就展区",
                "人造地球卫星展区", 
                "七大系列卫星展区",
                ],
            Current_Order_of_Visit_K:List[str]=[              # robot当前任务列表，完成一个就pop一个
                "东方红一号卫星展区", 
                "中国航天工程成就展区",
                "人造地球卫星展区", 
                "七大系列卫星展区",
                ],
            Trun_Direction_K:Dict={                      # robot在每个参观点的转向方向
                "东方红一号卫星展区":"middle", 
                "中国航天工程成就展区":"middle",
                "人造地球卫星展区":"middle", 
                "七大系列卫星展区":"middle",
                },
            EXTRA_INFORMATION_K:Dict={
                "东方红一号卫星展区":"机器人左手边有东方红一号卫星模型，其中包括一根实物天线。机器人右手边有科技专家展板，展示了对中国“两弹一星”事业有突出贡献的23位科技专家，包括孙家栋院士等校友。", 
                "中国航天工程成就展区":"机器人正对面有长征一号火箭的舱段、整流罩和火箭燃料储箱（实物）。机器人背后有长征系列运载火箭模型，包括长征一号、长征二号、长征五号等型号。",
                "人造地球卫星展区":"这一展区介绍了自1970年4月24日中国成功发射第一颗人造卫星以来形成的七个卫星系列：返回式遥感、科学技术试验、广播通信、气象、地球资源、导航定位和海洋。", 
                "七大系列卫星展区":"机器人左手边有风云四号气象卫星模型，是中国新一代静止轨道定量遥感气象卫星。机器人右手边有中国北斗导航卫星组网模型，展示了北斗卫星导航系统。机器人上方悬挂着墨子号模型，是世界首颗量子科学实验卫星模型。机器人身后有其他卫星与探月工程展品，包括返回式卫星、电子侦查卫星以及探月工程相关展品。",
                },
            TRANSITIONAL_SENTENCE_K:Dict={               # 对应于每一个讲解点的过渡句
                "东方红一号卫星展区":"", 
                "中国航天工程成就展区":"接下来，请大家随我一起参观中国航天工程成就部分。",
                "人造地球卫星展区":"接下来，请大家随我一起参观人造地球卫星部分。", 
                "七大系列卫星展区":"接下来，请大家随我一起参观我国的七大系列卫星。",
                },
            ACTOIN_DICT_K={                                   # 所有的动作及其索引
                '挥手动作':0,
                '礼仪讲解动作':7,
                '左手伸手指引':8,
                '右手伸手指引':9,
                '右手举起比1':10,
                '右手举起比2':11,
                '右手举起比3':12,
                '右手举起比5':13,
                '右手举起握拳':14,
                '左手平摊讲解动作':15,
                '右手平摊讲解动作':16,
                '左手前伸指引':17,
                '右手前伸指引':18,
                '先左后右平摊讲解动作':19,
                '双臂平举打开':20,
                '恢复行走状态':21,
                '礼仪讲解小幅度动作':22,
                '左手举起比1':23,
                '右手握拳在上左手张开做掌':24,
                '右手从1数到3':25,
                '右手举起比125':26,
                '左手伸手长指引':27,
                '右手伸手长指引':28,
                },
            TRANSITIONAL_ACTION_K:Dict={                 # 对应于每一个讲解点的过渡句的动作
                "东方红一号卫星展区":"", 
                "中国航天工程成就展区":"右手前伸指引",
                "人造地球卫星展区":"右手前伸指引", 
                "七大系列卫星展区":"右手前伸指引",
                },
            
            Mask:List[bool] = [False] * 4,                                 # 到过的地方就标记
            Onehot:List[bool] = [False] * 4,                               # 现在位于哪里
            Last_Play_Processor = None,
            
        ):

        self.id = GlobalValuesClass._id
        GlobalValuesClass._all_instances[self.id] = self  
        GlobalValuesClass._id += 1

        self.ROBOT_NAME = ROBOT_NAME
        
        self.Enable_QA = Enable_QA
        self.TAKE_ACTION_QA = TAKE_ACTION_QA
        self.TAKE_ACTION_EXPLAIN = TAKE_ACTION_EXPLAIN
        self.FACE_DETECT = FACE_DETECT
        self.FACE_RECOGNITION = FACE_RECOGNITION
        self.OBSTAC_STOP = OBSTAC_STOP
        self.POSE_DETECT = POSE_DETECT
        self.HANDHELD_DETECT = HANDHELD_DETECT
        self.ARM_ACTION = ARM_ACTION
        self.POSE_DETECT_KEYWORD = POSE_DETECT_KEYWORD
        self.HANDHELD_DETECT_FLAG = HANDHELD_DETECT_FLAG
        self.Action_from_User = Action_from_User
        self.EXPLAIN_SHOULD_ACTION = EXPLAIN_SHOULD_ACTION

        self.COMMENTARY_SPEECH = COMMENTARY_SPEECH
        self.SENTENCE_SUM = SENTENCE_SUM
        self.SENTENCE_INDEX = SENTENCE_INDEX
        self.LAST_BROAD_WORDS = LAST_BROAD_WORDS

        self.MODEL_TASK_TYPE = MODEL_TASK_TYPE
        self.MODEL_LLM_ANSWER = MODEL_LLM_ANSWER
        self.MODEL_BAN_OPENAI = MODEL_BAN_OPENAI
        self.STREAM_RETURN = STREAM_RETURN

        self.COUNT_OBS=COUNT_OBS
        self.COUNT_YOLO=COUNT_YOLO
        self.COUNT_HANDHELD=COUNT_HANDHELD
        self.COUNT_FACE=COUNT_FACE
        self.COUNT_POSE=COUNT_POSE

        self.LOW_COMPUTER_EXIST = LOW_COMPUTER_EXIST
        self.SOUND_INPUT_EXIST = SOUND_INPUT_EXIST
        self.SOUND_OUTPUT_EXIST = SOUND_OUTPUT_EXIST
        
        self.NAVI_START_FLAG= NAVI_START_FLAG
        self.NAVI_END_FLAG = NAVI_END_FLAG

        self.DURATION = DURATION
        self.THRESHOLD_AUDIO = THRESHOLD_AUDIO
        self.SOUND_CHANGE = SOUND_CHANGE
        
        if info is None:
            info = f"Hello! Description here." 
        self.info =  f"{self.__class__.__name__}"+ " " + name + ": " + info # 描述  
        
        self.is_Navigating = is_Navigating
        self.is_Depth_Obstacle = is_Depth_Obstacle
        self.is_Yolo_Obstacle = is_Yolo_Obstacle
        self.is_Explaining = is_Explaining
        self.is_QAing = is_QAing
        self.is_Interrupted = is_Interrupted
        self.is_Big_Face_Detected = is_Big_Face_Detected
        self.Big_Face_Area = Big_Face_Area
        self.Face_Name_Dict = Face_Name_Dict
        self.Recog_Count_Dict = {value: 0 for key, value in self.Face_Name_Dict.items() if key not in ['NOFACE', 'UNKNOWNPERSON']}
        
        self.Block_Navigation_Thread = Block_Navigation_Thread
        self.Current_Area = Current_Area     
        
        self.Destination_Area = Destination_Area
        self.Touchpad_Area = Touchpad_Area
        self.Current_Position = Current_Position
        self.Target_Position = Target_Position
        self.Index_of_Document = Index_of_Document
        self.Last_Sentence = Last_Sentence
        self.Interrupt_Area = Interrupt_Area
        self.Interrupt_Position = Interrupt_Position
        self.Last_Play_Processor = Last_Play_Processor
        self.card_id = card_id
        
        self.SCAN_DIRECTION = SCAN_DIRECTION
        self.HEAD_ANGLE = HEAD_ANGLE
        self.Origin_Order_of_Visit=[]
        
        # 'X' 相关信息
        self.Abb_of_Visit_X = Abb_of_Visit_X
        self.Index_of_Vist_X = Index_of_Vist_X
        self.Origin_Order_of_Visit_X = Origin_Order_of_Visit_X
        self.Current_Order_of_Visit_X = Current_Order_of_Visit_X
        self.Trun_Direction_X = Trun_Direction_X
        self.EXTRA_INFORMATION_X = EXTRA_INFORMATION_X
        self.TRANSITIONAL_SENTENCE_X = TRANSITIONAL_SENTENCE_X
        self.ACTOIN_DICT_X = ACTOIN_DICT_X
        self.TRANSITIONAL_ACTION_X = TRANSITIONAL_ACTION_X
        
        # 'K' 相关信息
        self.Abb_of_Visit_K = Abb_of_Visit_K
        self.Index_of_Vist_K = Index_of_Vist_K
        self.Origin_Order_of_Visit_K = Origin_Order_of_Visit_K
        self.Current_Order_of_Visit_K = Current_Order_of_Visit_K
        self.Trun_Direction_K = Trun_Direction_K
        self.EXTRA_INFORMATION_K = EXTRA_INFORMATION_K
        self.TRANSITIONAL_SENTENCE_K = TRANSITIONAL_SENTENCE_K
        self.ACTOIN_DICT_K = ACTOIN_DICT_K
        self.TRANSITIONAL_ACTION_K = TRANSITIONAL_ACTION_K

        self.Navi_start_Subscriber = Navi_start_Subscriber
        self.Navi_end_Subscriber = Navi_end_Subscriber
        self.Navi_target_Publisher = Navi_target_Publisher
        self.Stop_Publisher = Stop_Publisher
        self.Rotate_Publisher = Rotate_Publisher
        self.Touchpad_Navi_Subscriber = Touchpad_Navi_Subscriber
        self.Touchpad_Click_Publisher = Touchpad_Click_Publisher
        
        self.Arm_Action_Publisher = Arm_Action_Publisher

        self.Last_Area = Last_Area

        self.Mask = [False for _ in self.Origin_Order_of_Visit]
        self.Onehot = [False for _ in self.Origin_Order_of_Visit]

    def get_first_Current_Order_of_Visit_id(self, ):
        return self.Index_of_Vist[self.Current_Order_of_Visit[0]] if len(self.Current_Order_of_Visit) > 0 else None
    
    def set_ROBOT_NAME(self, new_ROBOT_NAME:bool=False) -> None:
        self.ROBOT_NAME = new_ROBOT_NAME
        
        if self.ROBOT_NAME == 'X':
            self.Abb_of_Visit = self.Abb_of_Visit_X
            self.Index_of_Vist = self.Index_of_Vist_X
            self.Origin_Order_of_Visit = self.Origin_Order_of_Visit_X
            self.Current_Order_of_Visit = self.Current_Order_of_Visit_X
            self.Trun_Direction = self.Trun_Direction_X
            self.EXTRA_INFORMATION = self.EXTRA_INFORMATION_X
            self.TRANSITIONAL_SENTENCE = self.TRANSITIONAL_SENTENCE_X
            self.ACTOIN_DICT = self.ACTOIN_DICT_X
            self.TRANSITIONAL_ACTION = self.TRANSITIONAL_ACTION_X
        elif self.ROBOT_NAME == 'K':
            self.Abb_of_Visit = self.Abb_of_Visit_K
            self.Index_of_Vist = self.Index_of_Vist_K
            self.Origin_Order_of_Visit = self.Origin_Order_of_Visit_K
            self.Current_Order_of_Visit = self.Current_Order_of_Visit_K
            self.Trun_Direction = self.Trun_Direction_K
            self.EXTRA_INFORMATION = self.EXTRA_INFORMATION_K
            self.TRANSITIONAL_SENTENCE = self.TRANSITIONAL_SENTENCE_K
            self.ACTOIN_DICT = self.ACTOIN_DICT_K
            self.TRANSITIONAL_ACTION = self.TRANSITIONAL_ACTION_K
        else:
            raise(f"ROBOT_NAME ERROR! (Wrong Value: {self.ROBOT_NAME}) Only support 'X' or 'K'.")
        
    
    def set_Enable_QA(self, new_Enable_QA:bool=False) -> None:
        self.Enable_QA = new_Enable_QA
        
    def set_TAKE_ACTION_QA(self, new_TAKE_ACTION_QA:bool=False) -> None:
        self.TAKE_ACTION_QA = new_TAKE_ACTION_QA

    def set_TAKE_ACTION_EXPLAIN(self, new_TAKE_ACTION_EXPLAIN:bool=False) -> None:
        self.TAKE_ACTION_EXPLAIN = new_TAKE_ACTION_EXPLAIN

    def set_FACE_DETECT(self, new_FACE_DETECT:bool=False) -> None:
        self.FACE_DETECT = new_FACE_DETECT
        
    def set_FACE_RECOGNITION(self, new_FACE_RECOGNITION:bool=False) -> None:
        self.FACE_RECOGNITION = new_FACE_RECOGNITION

    def set_OBSTAC_STOP(self, new_OBSTAC_STOP:bool=False) -> None:
        self.OBSTAC_STOP = new_OBSTAC_STOP

    def set_POSE_DETECT(self, new_POSE_DETECT:bool=False) -> None:
        self.POSE_DETECT = new_POSE_DETECT
        
    def set_HANDHELD_DETECT(self, new_HANDHELD_DETECT:bool=False) -> None:
        self.HANDHELD_DETECT = new_HANDHELD_DETECT

    def set_ARM_ACTION(self, new_ARM_ACTION:bool=False) -> None:
        self.ARM_ACTION = new_ARM_ACTION
    
    def set_POSE_DETECT_KEYWORD(self, new_POSE_DETECT_KEYWORD:str="") -> None:
        self.POSE_DETECT_KEYWORD = new_POSE_DETECT_KEYWORD
        
    def set_HANDHELD_DETECT_FLAG(self, new_HANDHELD_DETECT_FLAG:bool=False) -> None:
        self.HANDHELD_DETECT_FLAG = new_HANDHELD_DETECT_FLAG

    def set_EXPLAIN_SHOULD_ACTION(self, new_EXPLAIN_SHOULD_ACTION:str="") -> None:
        self.EXPLAIN_SHOULD_ACTION = new_EXPLAIN_SHOULD_ACTION

    def set_COMMENTARY_SPEECH(self, new_COMMENTARY_SPEECH:str="") -> None:
        self.COMMENTARY_SPEECH = new_COMMENTARY_SPEECH
    
    def set_SENTENCE_SUM(self, new_SENTENCE_SUM:str="") -> None:
        self.SENTENCE_SUM = new_SENTENCE_SUM

    def set_SENTENCE_INDEX(self, new_SENTENCE_INDEX:str="") -> None:
        self.SENTENCE_INDEX = new_SENTENCE_INDEX
        
    def set_LAST_BROAD_WORDS(self, new_LAST_BROAD_WORDS:str="") -> None:
        self.LAST_BROAD_WORDS = new_LAST_BROAD_WORDS

    def set_COUNT_OBS(self, new_COUNT_OBS:int) -> None:
        self.COUNT_OBS = new_COUNT_OBS

    def set_COUNT_YOLO(self, new_COUNT_YOLO:int) -> None:
        self.COUNT_YOLO = new_COUNT_YOLO
        
    def set_COUNT_HANDHELD(self, new_COUNT_HANDHELD:int) -> None:
        self.COUNT_HANDHELD = new_COUNT_HANDHELD

    def set_COUNT_FACE(self, new_COUNT_FACE:int) -> None:
        self.COUNT_FACE = new_COUNT_FACE

    def set_COUNT_POSE(self, new_COUNT_POSE:int) -> None:
        self.COUNT_POSE = new_COUNT_POSE

    def set_MODEL_TASK_TYPE(self, new_MODEL_TASK_TYPE:str="") -> None:
        self.MODEL_TASK_TYPE = new_MODEL_TASK_TYPE

    def set_MODEL_LLM_ANSWER(self, new_MODEL_LLM_ANSWER:str="") -> None:
        self.MODEL_LLM_ANSWER = new_MODEL_LLM_ANSWER
    
    def set_MODEL_BAN_OPENAI(self, new_MODEL_BAN_OPENAI:bool=False) -> None:
        self.MODEL_BAN_OPENAI = new_MODEL_BAN_OPENAI

    def set_STREAM_RETURN(self, new_STREAM_RETURN:bool=False) -> None:
        self.STREAM_RETURN = new_STREAM_RETURN

    def set_LOW_COMPUTER_EXIST(self, new_LOW_COMPUTER_EXIST:bool=False) -> None:
        self.LOW_COMPUTER_EXIST = new_LOW_COMPUTER_EXIST

    def set_SOUND_INPUT_EXIST(self, new_SOUND_INPUT_EXIST:bool=False) -> None:
        self.SOUND_INPUT_EXIST = new_SOUND_INPUT_EXIST

    def set_SOUND_OUTPUT_EXIST(self, new_SOUND_OUTPUT_EXIST:bool=False) -> None:
        self.SOUND_OUTPUT_EXIST = new_SOUND_OUTPUT_EXIST
        
    def set_NAVI_START_FLAG(self, new_NAVI_START_FLAG:bool=False) -> None:
        self.NAVI_START_FLAG = new_NAVI_START_FLAG
    
    def set_NAVI_END_FLAG(self, new_NAVI_END_FLAG:bool=False) -> None:
        self.NAVI_END_FLAG = new_NAVI_END_FLAG

    def set_DURATION(self, new_DURATION:int=2) -> None:
        self.DURATION = new_DURATION

    def set_THRESHOLD_AUDIO(self, new_THRESHOLD_AUDIO:int=2) -> None:
        self.THRESHOLD_AUDIO = new_THRESHOLD_AUDIO
        
    def set_SOUND_CHANGE(self, new_SOUND_CHANGE:int=15) -> None:
        self.SOUND_CHANGE = new_SOUND_CHANGE

    def set_is_Navigating(self, new_is_Navigating:bool=False) -> None:
        self.is_Navigating = new_is_Navigating
        if new_is_Navigating:
            self.is_Arrived = False
            
    def set_is_Depth_Obstacle(self, new_is_Depth_Obstacle:bool=False) -> None:
        self.is_Depth_Obstacle = new_is_Depth_Obstacle

    def set_is_Yolo_Obstacle(self, new_is_Yolo_Obstacle:bool=False) -> None:
        self.is_Yolo_Obstacle = new_is_Yolo_Obstacle
        
    def set_is_Explaining(self, new_is_Explaining:bool=False) -> None:
        self.is_Explaining = new_is_Explaining
        self.is_Navigating = False
        
    def set_is_QAing(self, new_is_QAing:bool=False) -> None:
        self.is_QAing = new_is_QAing
        
    def set_Action_from_User(self, new_Action_from_User:str="None") -> None:
        self.Action_from_User = new_Action_from_User

    def set_is_Interrupted(self, new_is_Interrupted:bool=False):
        self.is_Interrupted = new_is_Interrupted

    def set_is_Big_Face_Detected(self, new_is_Big_Face_Detected:bool=False) -> None:
        self.is_Big_Face_Detected = new_is_Big_Face_Detected
        
    def set_Big_Face_Area(self, new_Big_Face_Area:str="CENTER") -> None:
        self.Big_Face_Area = new_Big_Face_Area
        
    def set_Face_Name_Dict(self, new_Face_Name_Dict:dict) -> None:
        self.Face_Name_Dict = new_Face_Name_Dict
        
    def set_Recog_Count_Dict(self, new_Recog_Count_Dict:dict) -> None:
        self.Recog_Count_Dict = new_Recog_Count_Dict

    def set_Block_Navigation_Thread(self, new_Block_Navigation_Thread:bool=False)-> None:
        self.Block_Navigation_Thread = new_Block_Navigation_Thread

    def set_Current_Area(self, new_Current_Area:str="火箭展厅") -> None:
        self.Current_Area = new_Current_Area
        self.Mask[self.Origin_Order_of_Visit.index(self.Current_Area)] = True
        # self.Onehot[self.Origin_Order_of_Visit.index(self.Current_Area)] = True
        for i, area in enumerate(self.Origin_Order_of_Visit):
            self.Onehot[i] = area == self.Current_Area
        
        if self.Destination_Area == self.Current_Area:
            self.is_Arrived = True
            self.set_is_Navigating(False)
        
    def set_Last_Area(self, new_Last_Area:str):
        self.Last_Area = new_Last_Area
        
    def set_is_Arrived(self, new_is_Arrived:bool):
        self.is_Arrived = new_is_Arrived
        if self.is_Arrived:
            self.is_Navigating = False

        
    def set_Destination_Area(self, new_Destination_Area:str="航天器展厅") -> None:
        if new_Destination_Area not in self.Origin_Order_of_Visit and \
            '其他' not in new_Destination_Area and \
            '上一个' not in new_Destination_Area and \
            '下一个' not in new_Destination_Area:
            print(f"\033[33mWarning\033[0m {new_Destination_Area} 不在范围内")
            return "NotInArrage"
        def get_new_order(POLICY: str='SKIP') -> List[int]:
            if POLICY == "SKIP":  # 升序策略
                index = self.Origin_Order_of_Visit.index(new_Destination_Area)
                new_list = deepcopy(self.Origin_Order_of_Visit[index:])
                # print("\nnew_list", new_list)
            return new_list
                
    
        # if self.Destination_Area != new_Destination_Area:  # 重构list
        self.Current_Order_of_Visit = get_new_order(POLICY="SKIP")
        # print(self.Current_Order_of_Visit)
            
        self.Destination_Area = new_Destination_Area
        
        if self.Destination_Area != self.Current_Area:  # 未到
            self.is_Arrived = False
        else:
            self.is_Arrived = True

    def set_Touchpad_Area(self, new_Touchpad_Area:Optional[List[float]]) -> None:
        self.Touchpad_Area = new_Touchpad_Area
    
    def set_Current_Position(self, new_Current_Position:Optional[List[float]]) -> None:
        self.Current_Position = new_Current_Position

    def set_Target_Position(self, new_Target_Position:Optional[List[float]]) -> None:
        self.Target_Position = new_Target_Position

    def set_Index_of_Document(self, new_Index_of_Document:int = 0) -> None:
        self.Index_of_Document = new_Index_of_Document

    def set_Last_Sentence(self, new_Last_Sentence:str="") -> None:
        self.Last_Sentence = new_Last_Sentence

    def set_Interrupt_Area(self, new_Interrupt_Area:str="Gate") -> None:
        self.Interrupt_Area = new_Interrupt_Area

    def set_Interrupt_Position(self, new_Interrupt_Position:Optional[List[float]]) -> None:
        self.Interrupt_Position = new_Interrupt_Position

    def set_Last_Play_Processor(self, new_Last_Play_Processor):
        self.Last_Play_Processor = new_Last_Play_Processor

    def set_Navi_start_Subscriber(self, new_Navi_start_Subscriber):
        self.Navi_start_Subscriber = new_Navi_start_Subscriber
        
    def set_Navi_end_Subscriber(self, new_Navi_end_Subscriber):
        self.Navi_end_Subscriber = new_Navi_end_Subscriber
        
    def set_Navi_target_Publisher(self, new_Navi_target_Publisher):
        self.Navi_target_Publisher = new_Navi_target_Publisher
    
    def set_Stop_Publisher(self, new_Stop_Publisher):
        self.Stop_Publisher = new_Stop_Publisher
        
    def set_Rotate_Publisher(self, new_Rotate_Publisher):
        self.Rotate_Publisher = new_Rotate_Publisher
        
    def set_Touchpad_Navi_Subscriber(self, new_Touchpad_Navi_Subscriber):
        self.Touchpad_Navi_Subscriber = new_Touchpad_Navi_Subscriber
        
    def set_Touchpad_Click_Publisher(self, new_Touchpad_Click_Publisher):
        self.Touchpad_Click_Publisher = new_Touchpad_Click_Publisher

    def set_Arm_Action_Publisher(self, new_Arm_Action_Publisher):
        self.Arm_Action_Publisher = new_Arm_Action_Publisher

    def set_card_id(self,new_card_id:int) -> None:
        self.card_id = new_card_id
        
    def set_SCAN_DIRECTION(self,new_SCAN_DIRECTION:str='RIGHT') -> None:
        self.SCAN_DIRECTION = new_SCAN_DIRECTION
        
    def set_HEAD_ANGLE(self,new_HEAD_ANGLE:str='-30') -> None:
        self.HEAD_ANGLE = new_HEAD_ANGLE
     
    def update_all_attributes(self, new_attributes: dict) -> None:
        """
        通过字典方式更新所有实例变量的值。

        Args:
            new_attributes (dict): 包含要更新的实例变量及其新值的字典。

        """
        for attr, value in new_attributes.items():
            if hasattr(self, attr):
                if attr == "id":
                    print("Warning: The 'id' is not allowed to modified. Skip.")
                    continue
                setattr(self, attr, value)
            else:
                print(f"\nWarning: Attribute '{attr}' does not exist in {self.__class__.__name__}.\n")
    
    
    def add_var(self, var_name, value):
        """添加临时实例变量

        """
        setattr(self, var_name, value)
        
    def del_var(self, var_name):
        """删除临时实例变量

        """
        if hasattr(self, var_name):  # 检查实例是否包含指定的属性
            delattr(self, var_name)  # 删除实例变量
            
    def get_states_dict(self, ):
        return self.__dict__
    
    def print_all_status(self, ) -> None:
        import json
        from copy import deepcopy
        all_dict = deepcopy(self.__dict__)

        ignore_key = ['Mask', 'Onehot']

        for key in ignore_key:
            del all_dict[key]
        print("\033[1;33;47m GlobalValues--INFO--followings:\033[0m")
        print("\033[33m")
        print(json.dumps(all_dict, indent=4, ensure_ascii=False))
        print("\033[0m")
        print("\033[1;33;47m GlobalValues--INFO--above:\033[0m")
        print("\033[33m")   
    @classmethod
    def get_instance_by_id(cls, id):  # 根据ID获取实例
        return cls._all_instances.get(id, None)  

    @classmethod
    def get_count(cls):
        return cls._id

    @classmethod
    def create_instance(cls,**kwargs):   #  可以不用
        return cls(**kwargs)  # 返回当前类的实例
    
if __name__ == "__main__":
#    a = NavigationClass()
#     print(type(a.get_self_name()))

    STATUS = GlobalValuesClass(name="STATUS_1")
    STATUS_DICT = STATUS.get_states_dict()
    print(STATUS_DICT)
    
    print(STATUS.is_Explaining)
    print(STATUS_DICT['is_Explaining'])
    
    STATUS.is_Explaining = True
    print(STATUS.is_Explaining)
    print(STATUS_DICT['is_Explaining'])
    
    STATUS_DICT['is_Explaining']= False
    print(STATUS.is_Explaining)
    print(STATUS_DICT['is_Explaining'])
    
    STATUS.set_Destination_Area(new_Destination_Area="火箭展厅")
    
    STATUS.get_first_Current_Order_of_Visit_id()
    
    # a1 = GlobalValuesClass(name="a1")
    # a2 = GlobalValuesClass.create_instance(name="jaha")
    
    # a1.set_is_Explaining(False)  # 更新方式1
    # print(a1)
    
    # print(vars(a1))
    # print(vars(a2))
    # print(a2.__dict__)
    
    
    
    # aa = {'id': 100, 'is_Explaining': True, 'bb': '展厅', 'c': {'asd': 9}, 'e': ('asd', 'asda', 'er'), 'd': [1, 2, 3]}
    
    # T = {
    #     'id': 1, 
    #     'info': 'GlobalValuesClass jaha: Hello! Description here.', 
    #     'is_Navigating': False, 
    #     'is_Explaining': True, 
    #     'is_QAing': False, 
    #     'Current_Area': 'Gate', 
    #     'Destination_Area': '卫星展厅', 
    #     'Current_Position': None, 
    #     'Target_Position': None, 
    #     'Index_of_Document': 0, 
    #     'Last_Sentence': '', 
    #     'Interrupt_Area': None, 
    #     'Interrupt_Position': None
    #     }
    # a2.update_all_attributes(T)  # 更新方式2
    # print(a2.__dict__)
    # pass