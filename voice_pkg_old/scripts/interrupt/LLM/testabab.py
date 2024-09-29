import requests
import json
from datetime import datetime


def get_ababa65_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    API_KEY = config['abab65_api_key']
    group_id = config['abab65_group_id']
    return group_id, API_KEY

def abab_direct(model, system_prompt, query):
  group_id, api_key = get_ababa65_key()
  payload = {
    "bot_setting": [
        {
            # "bot_name": "MM智能助理",
            # "content": "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。",
            "bot_name": "小红",
            "content": system_prompt,
        }
    ],
    "messages": [
      {"sender_type": "USER", "sender_name": "小明", "text": query}
    ],
    "reply_constraints": {"sender_type": "BOT", "sender_name": "小红"},
    "model": model,
    "tokens_to_generate": 4096,
    "temperature": 0.01,
    # "top_p": 0.95,
  }
  
  headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}

  url = "https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId=" + group_id

  response = requests.request("POST", url, headers=headers, json=payload)
  return response.text
def abab_stream(model, system_prompt, query):
  group_id, api_key = get_ababa65_key()
  def parseChunkDelta(chunkStr):
      parsed_data = json.loads(chunkStr[6:])
      if "usage" in parsed_data:
          return  # 当前为流式完结chunk，无增量信息
      delta_content = parsed_data["choices"][0]["messages"]
      # print("delta message: ", delta_content)
      return delta_content[0]['text']


  url = "https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId=" + group_id

  payload = {
      "bot_setting": [
          {
              "bot_name": "小红",
              "content": system_prompt,
          }
      ],
      "messages": [{"sender_type": "USER", "sender_name": "小明", "text": query}],
      "reply_constraints": {"sender_type": "BOT", "sender_name": "小红"},
      "model": model,
      "stream": True,
      "tokens_to_generate": 2048,
      "temperature": 0.01,
      "top_p": 0.95,
  }
  headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}

  response = requests.request("POST", url, headers=headers, json=payload)

  response = requests.post(url, headers=headers, json=payload, stream=True)
  for chunk in response.iter_lines():
      if chunk:
          chunkStr = chunk.decode("utf-8")
          res = parseChunkDelta(chunkStr)
          if res:
            yield res


if __name__ == '__main__':
  query = '你好，你叫什么名字'
  system_prompt = "你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅，你的责任是服务这里的参观人员。他们现在对你发出提问，你需要根据参考文本回答所有关于机器人和该实验室相关的问题。参考文本上没有的信息尽量不要自行补充（但可以适当精简）。必要的时候回答你不能确定。你的回答要简洁，不能超过50个字。"
  model = "abab6.5-chat"
  res = abab_direct(model, system_prompt, query)
  res = abab_stream(model, system_prompt, query)
  for r in res:
    print(r, end='')