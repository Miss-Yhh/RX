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
  你身旁的游客现在对你说了一句话，你需要判断判断这句话是否存在指代消解问题。如果句子中包含代词或指代词，且没有在句子中或前文中清晰地指明其引用的具体对象，则回答“是”，否则回答“否”：
  
  ### 输出格式 ###
  输出只有一个字，或是“是”或是“否”。
  例如：
  游客的话：给我介绍一下实验室概况；
  回答：否。
  游客的话：那么它的优点是什么呢；
  回答：是。
  游客的话：你是谁，介绍一下你自己；
  回答：否。
  游客的话：这个东西真的这么厉害吗；
  回答：是。
  
  ### 游客的话 ###
  他们现在对你发出指令，你需要对他们的指令进行指代消解判断，请严格遵守以上的输出限制，不要输出额外的内容。
  游客的话：
  """
  
  querys = [
    '给我介绍一下玉兔号月球车',
    '它是什么时候发射到月球上去的',
    '他为什么叫玉兔号',
    '介绍一下你自己',
    '呃我觉得你可以介绍得更详细一点',
    '我嫩hi擦换成擦对的',
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
  