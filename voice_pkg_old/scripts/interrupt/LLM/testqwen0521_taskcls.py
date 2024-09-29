# -*- coding: UTF-8 -*-

from datetime import datetime
import random
from http import HTTPStatus
from openai import OpenAI
# import dashscope

model = 'wmjchat'
client_hpc = OpenAI(
        api_key="EMPTY",
        base_url="http://localhost:8000/v1",
)

# lingjie = "sk-5b22a660a4c945339ad2c6aa13fcf822"
# model = 'qwen1.5-14b-chat'
# client = OpenAI(
#     api_key=lingjie,  # 替换成真实DashScope的API_KEY
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope服务endpoint
# )

def qwen_direct(client, model, system_prompt, query):
    chatcompletion = client.chat.completions.create(
        model=model,
        messages=[{'role': 'system', 'content': system_prompt},
                  {'role': 'user', 'content': query}],
        temperature=0.01
    )
    return chatcompletion.choices[0].message.content


if __name__ == '__main__':
  system_prompt = '你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。'
  
  prompt = f"""
  ### 背景信息 ###
  你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅，你的主线任务是按照预定好的目标带游客按顺序参观这个展厅里的所有展区，包括服务及医疗机器人展区、宇航空间机构及控制展区、空间机器人展区、服务及医疗机器人展区、宇航空间机构及控制展区、工业及特种机器人展区、空间机器人展区、机器人基础功能部件展区、微纳及仿生机器人展区、实验室概况展区、实验室队伍展区、实验室宣传视频展区、未来展望展区、开放服务展区、领导关怀及荣誉展区
  
  ### 任务要求 ###
  你身旁的游客现在对你说了一句话，你需要对游客的话进行分类。
  
  1. 参观：当你识别到游客明确想要参观某个展厅（展区）时，比如游客说“带我参观医疗机器人展区吧”或“我想看看空间在轨服务机器人”或“没有问题了，继续参观下一个展厅吧”或“我想看看之前的展厅”或“带我最有意思的展区吧”，你需要将任务分类到参观，并输出“参观”；
  
  2. 继续：当你识别到游客明确想要打断你现在的讲解或者导航，比如“不要再继续讲解了”或“可以了，停下吧”或“我没有问题了，继续吧”或“不小心叫错你”，你需要将任务分类到继续，并输出“继续”；
  
  3. 动作：如果这句话好像是让你移动，比如“往前走一点“、”往前走一步”、“向左转”、“向右转”、“向后退”
  
  4. 问答：当你识别到用户的话不属于上面的任何一种，那么这句话很可能是一句提问，比如“介绍一下这个展品”或“长征七号为什么叫这个名字”或“我想了解一下人机协作型工业机器人”或“我觉得好像不是吧”，你需要将任务分类到问答，并输出“问答”；
  
  ### 输出格式 ###
  输出只有一行，只有一个词，或是参观或是回答或是继续
  例如：回答 
  
  ### 用户的话 ###
  他们现在对你发出指令，你需要对他们的指令进行分类，请严格遵守以上的输出限制，不要输出额外的内容。
  用户的话：
  """
  
  querys = [
    '带我去微纳及仿生机器人展区',
    '我看这个好像不是这个意思吧',
    '请问这是什么',
    '介绍一下月球车',
    '请带我去微纳及仿生机器人展区',
    '啊我不小心叫错你，没事',
    '带我去看医疗机器人',
    '长征系列火箭为什么叫这个名字',
    '往前来一点',
    '向后退',
    '小红，转个圈'
  ]
    
  for query in querys:
    print(query)
    time1 = datetime.now()
    reslist = qwen_direct(client_hpc, model, system_prompt, prompt+query)
    print(reslist)
    time2 = datetime.now()
    print(time2-time1)
  