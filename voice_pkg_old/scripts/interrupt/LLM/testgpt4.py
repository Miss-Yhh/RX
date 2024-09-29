"""openai.APIConnectionError: Connection error"""
import os
os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
"""openai.APIConnectionError: Connection error"""

import time
import yaml
import json
from openai import OpenAI

# Example of an OpenAI ChatCompletion request
# https://platform.openai.com/docs/guides/text-generation/chat-completions-api

def get_gpt4_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    openai_api_key = config['openai_api_key']
    return openai_api_key

def gpt_stream(model:str, system:str,query:str):
    open_api_key = get_gpt4_key()
    client = OpenAI(api_key=open_api_key)

    # send a ChatCompletion request to count to 100
    response = client.chat.completions.create(
        model=model,  # 'gpt-3.5-turbo' 'gpt-4'
        messages=[
            {'role':'system','content':system},
            {'role': 'user', 'content': query}
        ],
        temperature=0,
        stream=True  # again, we set stream=True
    )

    for chunk in response:
        if chunk:
            yield chunk.choices[0].delta.content  # extract the message)

def gpt_direct(model:str, system :str,query:str):
    open_api_key = get_gpt4_key()
    client = OpenAI(api_key=open_api_key)

    # send a ChatCompletion request to count to 100
    response = client.chat.completions.create(
        model=model,  # 'gpt-3.5-turbo' 'gpt-4'
        messages=[
            {'role':'system','content':system},
            {'role': 'user', 'content': query}
        ],
        temperature=0
    )

    return response.choices[0].message.content

if __name__ == '__main__':
    test_stream_bool = True

    if test_stream_bool:
        reslist = gpt_stream(model='gpt-4-turbo', query="你好")
        for r in reslist:
            if r:
                print(r, end='')
        print()
    else:
        reslist = gpt_direct(model='gpt-4-turbo', query="你好")
        print(reslist)