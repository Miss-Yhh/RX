# python3
import json
from openai import OpenAI
from datetime import datetime


def get_ds_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    deepseek_api_key = config['deepseek_api_key']
    return deepseek_api_key

def get_dk_stream(system_prompt, query):
  ds_api_key = get_ds_key()
  print(ds_api_key)
  client = OpenAI(api_key=ds_api_key, base_url="https://api.deepseek.com/")
  response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ],        
    temperature=0.01,
    stream=True  # again, we set stream=True
  )
  for chunk in response:
    if chunk:
      yield chunk.choices[0].delta.content  # extract the message)

def get_dk_direct(system_prompt, query):
  ds_api_key = get_ds_key()
  client = OpenAI(api_key=ds_api_key, base_url="https://api.deepseek.com/")
  response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ],        
    temperature=0.01,
    stream=False  # again, we set stream=True
  )
  return response.choices[0].message.content


if __name__ == '__main__':
    test_stream_bool = False

    if test_stream_bool:
        reslist = get_dk_stream(system_prompt="",query="你好")
        for r in reslist:
            if r:
                print(r, end='')
        print()
    else:
        reslist = get_dk_direct(system_prompt="",query="你好")
        print(reslist)
            
