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

lingjie = "sk-5b22a660a4c945339ad2c6aa13fcf822"
model = 'qwen1.5-14b-chat'
client = OpenAI(
    api_key=lingjie,  # 替换成真实DashScope的API_KEY
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope服务endpoint
)

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
  你身旁的游客现在对你说了一句话，这句话是代表着一个动作指令。
  
  而你会的动作是以下四个：前进、后退、左转、右转；
  
  你需要将动作分类到如下的四个动作之一
  
  1. 前进：当你识别到这句话是想要你前进，比如“向前走一步”，“向前走”，“前进”，你需要将这个动作指令分类为前进，并输出“前进”；
  
  2. 后退：当你识别到游客是想要你后退，比如“后退”或“向后退”或“向后站”或“往后站一步”，你需要将动作分类到后退，并输出“后退”；
  
  3. 左转：如果这句话好像是让你左转，比如“向左转“、”往左边来点”、“看左边”、“来左边一点”、“向左旋转”，你需要将动作分类到左转，并输出“左转”；
  
  4. 右转：如果都不属于上面的动作，那么这个动作很可能是向右转，比如“向右转”，“右转”、“看右边”，你需要将动作分类到右转，并输出“右转”；
  
  5. 其他：如果你发现这句话很显然不是一个动作，那么请勇敢地指出用户的错误，并输出“其他”
  
  ### 输出格式 ###
  输出只有一行，只有一个词，或是前进、或是后退、或是左转、或是右转、或是其他
  例如：前进
  
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
    reslist = qwen_direct(client, model, system_prompt, prompt+query)
    print(reslist)
    time2 = datetime.now()
    print(time2-time1)
  