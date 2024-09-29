from datetime import datetime
import os
import yaml
from .testqwen1 import qwen_stream_once

def _llm_api(system_prompt=None, query=None, model='gpt-4', fewshots=None):
    if model == 'qwen1_5':
        reslist = qwen_stream_once(query=query)
    else:
        assert("The model you entered is not supported, please select the following model: gpt-4 gpt-3.5-turbo chatglm")
    result = ''
    for r in reslist:
        if r:
            result += str(r)
    return result


def task_class(text=None, model='gpt-4'):
    # 在代码中写死的prompt
    # query = _prompt_construct(text)

    # 根据配置文件灵活改写的prompt
    # config_path = "/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/prompt_config.yaml"
    # query = _prompt_construct_by_config(txt=text, config_path=config_path)
    
    system_prompt, prompt = _prompt_taskcls_only(exhibition=exhibition, extra_information=extra_information)

    # print("任务分类Prompt: ", query)
    result = _llm_api(system_prompt=system_prompt, query=prompt+text, model='qwen1_5_direct')
    print("任务分类模型结果：", result, datetime.now())

    legal_task_types = ['问答', '休眠', '参观', '继续', '音量变大', '音量变小']
    if any(legal_task_type in result for legal_task_type in legal_task_types):
        return result

    return "任务分类失败！大模型的错误输出是：" + result


def _prompt_taskcls_only(exhibition=None, extra_information=""):
    system_prompt = '你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。'
  
    prompt = f"""
    ### 背景信息 ###
    你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅，你的主线任务是按照预定好的目标带游客按顺序参观这个展厅里的所有展区，包括服务及医疗机器人展区、宇航空间机构及控制展区、空间机器人展区、服务及医疗机器人展区、宇航空间机构及控制展区、工业及特种机器人展区、空间机器人展区、机器人基础功能部件展区、微纳及仿生机器人展区、实验室概况展区、实验室队伍展区、实验室宣传视频展区、未来展望展区、开放服务展区、领导关怀及荣誉展区
    
    ### 当前位置 ###
    你现在处在的位置是{exhibition}，有关这个位置的信息是：{extra_information}。

    ### 任务要求 ###
    你问你身旁的游客“大家有什么问题或指令吗？”，身旁的游客现在对你说了一句话，你需要对游客的话进行分类。

    1. 参观：当你识别到游客明确想要参观某个展厅（展区）时，比如游客说“带我参观医疗机器人展区吧”或“我想看看空间在轨服务机器人”或“没有问题了，继续参观下一个展厅吧”或“我想看看之前的展厅”或“带我最有意思的展区吧”，你需要将任务分类到参观，并输出“参观”；

    2. 继续：当你识别到游客明确想要让你继续之前的任务，比如“没有了”或“我没有问题了，继续吧”或“不小心叫错你”，你需要将任务分类到继续，并输出“继续”；
    
    3. 休眠：当你识别到游客不需要你继续带领游客参观了，比如“休眠去吧”或“停止参观吧”或“我不需要你了”，你需要将任务分类到休眠，并输出“休眠”；
    
    4. 音量变大或音量变小：当你识别到游客想要增大你的音量时，比如“你的声音太小了，请调大音量”，你需要将任务分类到音量变大，并输出“音量变大”，当你识别到游客想要减小你的音量时，比如“你的声音太大了，请调小音量”，你需要将任务分类到音量变小，并输出“音量变小”；

    5. 问答：当你识别到游客的话不属于上面的任何一种，那么这句话很可能是一句提问，比如“介绍一下这个展品”或“长征七号为什么叫这个名字”或“我想了解一下人机协作型工业机器人”或“我觉得好像不是吧”，你需要将任务分类到问答，并输出“问答”；
    
    例如：游客的话：带我参观医疗机器人展区吧，你的回答：参观；
    例如：游客的话：我想看看空间在轨服务机器人，你的回答：参观；
    例如：游客的话：没有问题了，继续参观下一个展厅吧，你的回答：参观；
    例如：游客的话：我想看看之前的展厅，你的回答：参观；
    例如：游客的话：带我最有意思的展区吧，你的回答：参观；
    例如：游客的话：带我去看看实验室的老师，你的回答：参观；
    例如：游客的话：带我去参观一下那边的鸟和青蛙，你的回答：参观；
    例如：游客的话：没有了，你的回答：继续；
    例如：游客的话：我没有问题了，继续吧，你的回答：继续；
    例如：游客的话：不小心叫错你，你的回答：继续；
    例如：游客的话：休眠去吧，你的回答：休眠；
    例如：游客的话：停止参观吧，你的回答：休眠；
    例如：游客的话：我不需要你了，你的回答：休眠；
    例如：游客的话：你的声音太小了，请调大音量，你的回答：音量变大；
    例如：游客的话：你的声音太大了，请调小音量，你的回答：音量变小；
    例如：游客的话：介绍一下这个展品，你的回答：问答；
    例如：游客的话：长征七号为什么叫这个名字，你的回答：问答；
    例如：游客的话：我想了解一下人机协作型工业机器人，你的回答：问答；
    例如：游客的话：我觉得好像不是吧，你的回答：问答；

    ### 输出格式 ###
    输出只有一行，只有一个词，或是参观或是问答或是继续
    例如：问答

    ### 游客的话 ###
    他们现在对你发出指令，你需要对他们的指令进行分类，请严格遵守以上的输出限制，不要输出额外的内容。
    游客的话：
    """
    return system_prompt, prompt

