from datetime import datetime
import random
from http import HTTPStatus
from openai import OpenAI
# import dashscope

lingjie = "sk-5b22a660a4c945339ad2c6aa13fcf822"

def qwen_stream_once(query='', system_prompt='', history_query='', history_answer=''):
    # hpc+本地端口转发
    client = OpenAI(
        api_key="EMPTY",
        base_url="http://localhost:9833/v1",
    )
    model = 'wmjchat'
    # 使用边缘机
    # client = OpenAI(
    #     api_key="EMPTY",
    #     base_url="http://192.168.31.90:9833/v1",
    # )
    # model = 'wmjchat'
    chatcompletion = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': history_query},
            {'role': 'assistant', 'content': history_answer},
            {'role': 'user', 'content': query}
        ],
        temperature=0.01,
        stream=True,
        presence_penalty=2.0,
    )
    for chunk in chatcompletion:
       if chunk:
          yield chunk.choices[0].delta.content 
