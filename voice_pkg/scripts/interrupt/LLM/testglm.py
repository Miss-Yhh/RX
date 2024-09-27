"""openai.APIConnectionError: Connection error"""
import os
os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
"""openai.APIConnectionError: Connection error"""

import json
from zhipuai import ZhipuAI

def get_zhipu_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    zhipu_api_key = config['zhipu_apikey']
    return zhipu_api_key

def glm_stream(query, system_prompt=None, few_shots=None):
    zhipu_api_key = get_zhipu_key()
    client = ZhipuAI(api_key=zhipu_api_key) # 填写您自己的APIKey

    if system_prompt is None:
        system_prompt = ""
    assert type(system_prompt) is str
    if few_shots is None:
        few_shots = []
    assert type(few_shots) is list

    content = system_prompt

    for i in range(len(few_shots)):
        content += f"输入：{few_shots[i][0]}\n"
        content += f"输出：{few_shots[i][1]}\n"

    content += f"输入：{query}\n输出："

    conversations = [{'role':'system','content':system_prompt},
            {'role': 'user', 'content': query}]
    
    response = client.chat.completions.create(
        model="glm-3-turbo", # 填写需要调用的模型名称
        messages=conversations,
        stream=True
    )

    for resp in response:
        if resp:
            yield resp.choices[0].delta.content

def glm_direct(query, system_prompt=None, few_shots=None):
    zhipu_api_key = get_zhipu_key()
    client = ZhipuAI(api_key=zhipu_api_key) # 填写您自己的APIKey

    if system_prompt is None:
        system_prompt = ""
    assert type(system_prompt) is str
    if few_shots is None:
        few_shots = []
    assert type(few_shots) is list

    content = system_prompt

    for i in range(len(few_shots)):
        content += f"输入：{few_shots[i][0]}\n"
        content += f"输出：{few_shots[i][1]}\n"

    content += f"输入：{query}\n输出："

    conversations = [{'role':'system','content':system_prompt},
            {'role': 'user', 'content': query}]
    
    response = client.chat.completions.create(
        model="glm-3-turbo", # 填写需要调用的模型名称
        messages=conversations,
    )

    return response.choices[0].message.content

if __name__ == 'main':
    test_stream_bool = False

    if test_stream_bool:
        reslist = glm_stream(query="你好")
        for r in reslist:
            if r:
                print(r, end='')
        print()
    else:
        print("AAAAAAAAAAAAAA")
        reslist = glm_direct(query="你好")
        print(reslist)
