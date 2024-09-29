import asyncio
import json
import os
import subprocess
import time
import httpx
from hashlib import sha256
from openai import OpenAI
from kedaxunfei_iat.iat_as_service_iter import iat_web_api
from zhipuai import ZhipuAI
from datetime import datetime
Last_Play_Processor = None
from datetime import datetime
import json
import jieba.posseg as pseg


class QAwmj:
  def __init__(self, yjnpath, wmjpath) -> None:
    keyresults0, docresults0 = self.readjson(yjnpath)
    keyresults1, docresults1 = self.readjson_gpt4(wmjpath)
    self.jsondata = {'关键词':keyresults0+keyresults1, '描述内容':docresults0+docresults1}
  
  def readjson(self, path):
    keyresults, docresults = [], []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    def find_values(json_data, key, para):
        """递归搜索所有键为 key 的值"""
        if isinstance(json_data, dict):  # 如果当前数据是字典
            for k, v in json_data.items():
                if k == key:
                    keyresults.append(v)  # 如果找到了匹配的键，添加其值到结果列表
                if k == para:
                    docresults.append(v)  # 如果找到了匹配的键，添加其值到结果列表
                find_values(v, key, para)  # 递归搜索该键的值
        elif isinstance(json_data, list):  # 如果当前数据是列表
            for item in json_data:
                find_values(item, key, para)  # 递归搜索列表中的每一个元素
    find_values(json_data=data, key='name', para='introduction')
    return keyresults, docresults
  
  def readjson_gpt4(self, jsonpath):
    with open(jsonpath, 'r') as f:
      data = json.load(f)
    keys = list(data.keys())
    values = list(data.values())
    return keys, values

  def manyquerykeys_in_para(self, keywords, para):
    count = 0
    for key in keywords:
        if key in para:
           count += 1
    return count == len(keywords)
             
  def get_re_query(self, query='说说机器人是什么'):
    def extract_nouns(sentence):
        words = pseg.cut(sentence)
        nouns = [word.word for word in words if word.flag.startswith('n')]
        return nouns

    query_keywords = list(set(extract_nouns(query)))
    match_keypara = []
    for i in range(len(self.jsondata['关键词'])):
      keyword = self.jsondata['关键词'][i]
      para = self.jsondata['描述内容'][i]
      for query_keyword in query_keywords:
        if query_keyword in keyword or self.manyquerykeys_in_para(query_keywords, para):
          match_keypara.append(keyword+":"+para)
    match_keypara = list(set(match_keypara))
    if len(match_keypara) == 0:
      return ""
    else:
      res = ";\n\n".join(match_keypara)
      return res  # list

def text2speech(text='', index=0, card_id=0):
    timewmj = str(datetime.now().minute) + str(datetime.now().second)
    savepath = f'/home/kuavo/catkin_dt/src/voice_pkg/temp_record_chat/chat_{timewmj}.mp3'
    
    ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/tts_as_service.py", text, savepath])
    while ttsproc.poll() is None:
        time.sleep(0.2)
    # 转为raw的格式
    savepath_pcm = savepath.replace(".mp3", "_pcm.wav")
    cmd = f"ffmpeg -loglevel quiet -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -filter:a \"volume=15dB\" -y {savepath_pcm}"
    exit_status = os.system(cmd)

    global Last_Play_Processor
    while Last_Play_Processor and Last_Play_Processor.poll() is None:
        # print('last process is working, waiting')
        time.sleep(0.2)
    playproc = subprocess.Popen(["aplay", "-D", f"plughw:{card_id},0", '-f', 'S16_LE', '-r', '16000', '-c', '1', f'{savepath_pcm}'])

    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            # print('play process is working')
            time.sleep(0.2)
        Last_Play_Processor = None
    else:
        # 异步播放:
        Last_Play_Processor = playproc
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'

class OpenAiBuilder:
    username = None
    password = None

    def __init__(self, base_url):
        self.base_url = base_url
        self.cookies = None

    def login(self, username, password=None, password_path=None):
        if password_path:
            with open(password_path, "r") as f:
                password = f.read().strip()
        password = sha256(password.encode("utf-8")).hexdigest()
        assert password, "password or password_path must be provided"

        login = httpx.post(
            f"{self.base_url}/api/login",
            json={"name": username, "password_hash": password},
        )
        if login.status_code != 200:
            raise Exception(f"Failed to login: {login.text}")
        self.cookies = {key: value for key, value in login.cookies.items()}

    def build(self) -> OpenAI:
        http_client = httpx.Client(cookies=self.cookies)
        client = OpenAI(
            base_url=f"{self.base_url}/api/v1",
            api_key="token-abc123",
            http_client=http_client,
        )

        return client

def stream_chat(client: OpenAI, prompt, system_prompt):
    completion = client.chat.completions.create(
        model="huozi",
        messages=[
            {"role": "系统", "content": system_prompt},
            {"role": "用户", "content": prompt},
        ],
        temperature=0,
        extra_body={"stop_token_ids": [57000, 57001]},
        stream=True  # this time, we set stream=True
    )
    for chunk in completion:
        c = chunk.choices[0].delta.content
        if c != None: 
            yield c

def glm_stream(query, system_prompt=None, few_shots=None, stream_bool=True):
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as f:
      zhipu_api_key = json.load(f)
      zhipu_api_key = zhipu_api_key['zhipu_apikey']
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

    conversations = [{"role": "user", "content": content}]
    
    response = client.chat.completions.create(
        model="glm-3-turbo", # 填写需要调用的模型名称
        messages=conversations,
        stream=stream_bool
    )

    if stream_bool:
        for resp in response:
            c = resp.choices[0].delta.content
            if c:
                yield c
    else:
        return response.choices[0].message.content

if __name__ == "__main__":
    retrieve_object = QAwmj('/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/json/hh.json', '/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/json/wmj.json')
    system_prompt = "你是哈工大研发的一个航天馆展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。"
    
    splitters = [',', ';', '.','!','?',':', '，', '。', '！', "'", '；', '？', '：', '/'] # 遇到这些符号就拆分句子
    numbers = [str(c) for c in range(10)] # 遇到数字不拆分句子

    # 公网api
    # username = "陈一帆"
    # url = "https://huozi.8wss.com"
    # builder = OpenAiBuilder(url)
    # builder.login(username, password="123456")
    # client = builder.build()

    # 一帆的本地部署
    openai_api_key = "EMPTY"
    openai_api_base = "http://localhost:8000/v1"
    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    while 1:
        # query = iat_web_api(input='ding', iter=3, card=0)
        query = input("input: ")
        time1 = datetime.now()
        print(time1)
        summary_prompt = retrieve_object.get_re_query(query)
        
        question = f"请参考文本:“{summary_prompt}”，回答问题:“{query}”。请给出问题的答案，注意：回答不要超过50个汉字，而且回答要完整。如果根据参考文本无法给出答案，不要说什么“根据提供的文本无法回答”而是直接根据你的常识直接给出简洁的答案。"
        question1 = f'''
                  你是哈尔滨工业大学航天馆的展厅机器人，负责外来游客的导游任务。。
                  你的主线任务是按照预定好的目标带游客按顺序参观航天馆的所有展厅，包括东方红一号展区、孙家栋院士成就展区、中国航天工程成就展区、中国人造地球卫星展区、气象卫星风云四号展区、北斗导航卫星展区、科学实验卫星墨子号展区、气象卫星风云一号展区、返回式卫星尖兵一号展区、电子侦察卫星长空一号展区、中国探月工程展区、高分专项工程展区、中国载人航天工程展区、载人飞船神舟五号展区、航天员展区、深空探测展区，同时游客可能随时打断你，你需要对游客的意图进行识别并分类。
                  当你识别到游客明确想要参观某个展厅时，比如游客说“带我参观中国探月工程展区吧”或“我想看看东方红一号卫星”、“继续参观下一个展厅吧”或“我想看看之前的展厅”，你需要将任务分类到“参观”，进而终止当前的主线任务，导航到游客指定的展厅，并输出“参观 孙家栋院士成就展区”或“参观 中国人造地球卫星展区”或“参观 上一个”或“参观 下一个”; 
                  当你识别到游客提出了一个问题时，比如游客说“我想了解一下嫦娥二号卫星”（明确说明展品名称（例如“北斗卫星”））、“介绍一下这个展品”（用户可能在用手指指向某一个展品（只是说了“这个”）），你需要将任务分类到“问答”，进而执行问答任务，并根据游客是不是有可能正在指着一个展品，输出“问答”或“问答 指着”;
                  当你识别到游客想要打断你正在执行的任务时，比如“不要再继续讲解了”或“可以了，停下吧”或“原地休眠”，你需要将任务分类到“休眠”，进而停止你所有正在执行的任务，进入等待状态，并输出“休眠”；
                  当你识别到游客想让你继续主线任务时，比如“没有了”或“我没有问题了”或“继续参观吧”，你需要将任务分类到继续，从而继续执行主线任务，并输出“继续”。
                  你只能输出一种最强烈的意图，以下是游客的指令，请你对其进行意图分类：{query}
                  '''
        print("---------", question, "----------\n")
        generator_wmj = stream_chat(client, question, system_prompt)
        # generator_wmj = glm_stream(prompt)
        print(query)
        for c in generator_wmj:
          # print("time=============", datetime.now() - time1)
          print(c, end="")
        
        print("\n--------over-------\n")
        # sentence = "" # 用于存储句子
        # pre_c = '' # 用于存储上一个字符

        # 遍历文本，切分段落为句子
        # for c in generator_wmj:
        #     sentence += c
        #     # 一旦碰到标点符号，就判断目前的长度
        #     if c in splitters and len(sentence) > 8:
        #         if pre_c in numbers:
        #             continue
        #         text2speech(sentence, 0, 0)
        #         sentence = ""
        # if sentence:
        #     text2speech(sentence, 0, 0)
        # while Last_Play_Processor.poll() is None:
        #     # print('play process is working')
        #     time.sleep(0.2)
        # print("over")
        