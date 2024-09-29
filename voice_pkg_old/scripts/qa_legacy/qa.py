
from datetime import datetime
import os
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
# import redis
import re
import requests
# from volcengine.maas import MaasService, MaasException, ChatRole
# from redis_utils import redis_getall_history
# from utils import stop_detect
# import jieba.posseg as pseg
# from zhkeybert import KeyBERT, extract_kws_zh
from zhipuai import ZhipuAI
import json

# https://pypi.tuna.tsinghua.edu.cn/simple

def get_zhipu_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    zhipu_api_key = config['zhipu_apikey']
    return zhipu_api_key

# 创建一个 Redis 连接对象
# r = redis.Redis(host='localhost', port=6379, db=0)

# 火山引擎的配置
VOLC_ACCESSKEY='xxx'
VOLC_SECRETKEY='yyy'

# 数据路径
document_data_path = os.path.join("/home/kuavo/catkin_dt/src/voice_pkg/scripts/qa_legacy/qa_data/documents_lecture_all-v4.csv")
doc_d, key_d = '描述内容', '关键词'  # pandas的属性列名

embedding_path = os.path.join("/home/kuavo/catkin_dt/src/voice_pkg/scripts/qa_legacy/qa_data/doc_emb_key_emb_cls_pooling-v5-small.npz")
doc_e, key_e = 'doc_emb', 'key_emb'  # npz的keys名

# 模型路径
bge_ckptpath = "BAAI/bge-small-zh-v1.5"

# 使用本地下载的模型初始化KeyBERT模型
# keybertpath = os.path.join("/home/kuavo/catkin_dt/src/voice_pkg/scripts/qa_legacy/paraphrase-multilingual-MiniLM-L12-v2")
# kw_model = KeyBERT(model=keybertpath)
# print("paraphrase-multilingual-MiniLM-L12-v2 加载完毕 ...")

# bing搜索的配置
SERPAPI_KEY='mmm'

# request 参数
headers = {
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5'
}
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890'
}
bing_truncate_config = {
    'max_doc_len':8192, 
    'min_doc_len':1
}
class SyntaxExtractor:
    def __init__(self, config):
        self.max_doc_len = config["max_doc_len"]
        self.min_doc_len = config["min_doc_len"]
        self.zh_stopwords = ['版权归原作者所有，如有侵权，请联系我们', " 您的浏览器不支持 video 标签", "\r",
                             "特别声明：以上内容(如有图片或视频亦包括在内)为自媒体平台“网易号”用户上传并发布，本平台仅提供信息存储服务。"]
        self.en_stopwords = [
            "Stack Exchange network consists of 183 Q&A communities including Stack Overflow, the largest, most trusted online community for developers to learn, share their knowledge, and build their careers.",
            "Do Not Sell My Personal Information",
            "The technical storage or access that is used exclusively for anonymous statistical purposes.",
            "Without a subpoena, voluntary compliance on the part of your Internet Service Provider, or additional records from a third party, information stored or retrieved for this purpose alone cannot usually be used to identify you.",
            "All rights reserved.",
            "Reddit, Inc. © 2023.",
            "We use cookies to help us to deliver our services. We'll assume you're ok with this, but you may change your preferences at our Cookie Centre.",
        ]

        self.extract = lambda lang, html, loosen=False: self.zh_extract(html, loosen) if lang == "zh" else self.en_extractor(html, loosen)

    def serp_api(self, query: str, language:str):
        params = {"engine": "bing", "q": query, "api_key": SERPAPI_KEY}
        response = requests.get("https://serpapi.com/search", params=params)
        if response.status_code != 200:
            raise Exception("serpapi returned %d\n%s" % (response.status_code, response.text))
        result = response.json()
        urls, info = [], []
        if "organic_results" not in result:
            return [], []

        for item in result['organic_results']:
            if "title" not in item or "link" not in item or "snippet" not in item:
                continue
            info.append({"title": item['title'], "url": item['link'], "snip": item['snippet']})
            urls.append(item["link"])

        return urls, info

    def get_all_text(self, url):
        try:
            response = requests.get(url, verify=False, headers=headers, proxies=proxies, timeout=0.1)
        
            # 尝试从Content-Type中获取字符集，如果没有找到，则默认使用UTF-8
            charset = response.apparent_encoding or 'utf-8'

            # 根据检测到的字符集解码响应内容
            html = response.content.decode(charset, 'ignore')

            # 进行中文的filter
            return self.zh_extract(html)
        except requests.exceptions.ConnectTimeout:
            print('connection timeout!!!')
            return None
        except:
            return None

    def zh_extract(self, html, loosen=False):
        soup = BeautifulSoup(html, 'lxml')
        a = soup.get_text()
        b = a.replace(" ", " ").replace("​", " ").replace("﻿", " ")
        c = re.sub("((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*",
                   " ", b)
        for i in self.zh_stopwords:
            c = c.replace(i, "")

        raw = c.split("\n")

        filter_ = set()
        paragraphs = []
        
        char_min_num = 15 if not loosen else 10
        punctuation_min_num = 4 if not loosen else 2

        for index, text in enumerate(raw):
            if 1 < index < len(raw) - 1 and len(raw[index - 1].strip()) >= char_min_num and len(raw[index + 1].strip()) >= char_min_num and \
                    sum([text.count(i) for i in "，。？；！"]) > punctuation_min_num:
                paragraphs.append(text.strip())
                continue

            if len(text.strip()) < char_min_num:
                filter_.add(text)
                continue

            if sum([text.count(i) for i in "，。？；"]) <= punctuation_min_num:
                filter_.add(text)
                continue

            paragraphs.append(text.strip())

        doc = "\n".join(paragraphs)

        doc = self.truncate_zh_doc(doc, self.max_doc_len, self.min_doc_len)

        return doc
    
    def truncate_zh_doc(self, doc: str, max_doc_len: int = None, min_doc_len: int = None):
        if min_doc_len is not None and len(doc) <= min_doc_len:
            return None

        if max_doc_len is None or len(doc) <= max_doc_len:
            return doc

        doc = doc[:max_doc_len]

        index = len(doc) - 1
        while index >= 0:
            if doc[index] in "。！？\n":
                return doc[:index + 1]
            else:
                index -= 1

        return doc

# 加载bge模型
print("加载bge模型 ...")
ppp = "catkin_dt/src/checkpoints/bge_small_zh_v1.5/models--BAAI--bge-small-zh-v1.5/snapshots/7999e1d3359715c523056ef9478215996d62a620"
tokenizer = AutoTokenizer.from_pretrained(ppp)#, cache_dir='/home/kuavo/catkin_dt/src/checkpoints/bge_small_zh_v1.5')
model = AutoModel.from_pretrained(ppp)#, cache_dir="/home/kuavo/catkin_dt/src/checkpoints/bge_small_zh_v1.5")

# 加载文本的embedding
doc_emb_key_emb = np.load(embedding_path)

# 加载文本
df_docu = pd.read_csv(document_data_path)

# 加载bge方法
def get_bge_query(sentence = '说说机器人是什么'):
    # 新的逻辑：返回关键词和“描述内容”的top1
    model.eval()
    # Tokenize sentences
    encoded_input = tokenizer([sentence], max_length=512, padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)
        # Perform pooling. In this case, cls pooling.
        sentence_embeddings = model_output[0][:, 0]
    
    # normalize embeddings
    sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
    
    # cal sim sentence
    key_res = torch.mm(torch.Tensor(doc_emb_key_emb[key_e]), sentence_embeddings.T)
    doc_res = torch.mm(torch.Tensor(doc_emb_key_emb[doc_e]), sentence_embeddings.T)

    ind_top1_key = int(key_res.argmax())
    ind_top1_doc = int(doc_res.argmax())

    keylist = df_docu[key_d].tolist()
    doclist = df_docu[doc_d].tolist()
    return keylist[ind_top1_key]+':'+doclist[ind_top1_key], keylist[ind_top1_doc]+':'+doclist[ind_top1_doc], float(key_res.max()), float(doc_res.max())

# 加载bing方法
def bing_test(query):
    # 不要vpn
    # 返回时间改为100ms
    # 逻辑改为：接受返回的任何网页
    # 使用bing搜索引擎，保证网页内容不敏感
    syn = SyntaxExtractor(config=bing_truncate_config)
    urls, info = syn.serp_api(query, 'zh')
    # 对返回的结果中的url进行request 获取url的文档的中文内容
    # for url in urls[:4]:
    #     # print(url)
    #     filter_text = syn.get_all_text(url)
    #     if filter_text:
    #         return filter_text
    # 如果没有找到相关的文档，返回snippet
    snip = []
    for i in info:
        snip.append(i['snip'])
    snip_res = '\n'.join(snip)
    return snip_res

# 加载GLM-api
# maas = MaasService('maas-api.ml-platform-cn-beijing.volces.com', 'cn-beijing')
# print("GLM-api加载完毕 ...")

# maas.set_ak(VOLC_ACCESSKEY)
# maas.set_sk(VOLC_SECRETKEY)

# 流式返回GLM-api结果
def test_stream_chat(maas, prompt, querys, answers):
    # print(f'正在进行第{len(querys)}轮对话:')
    # print('-'*10)
    # print(prompt)
    conversations = []
    for i in range(len(querys)):
        conversations.append({
                "role": ChatRole.USER,
                "content": querys[i]
            })
        conversations.append({
                "role": ChatRole.ASSISTANT,
                "content": answers[i]
            })
    conversations.append({
            "role": ChatRole.USER,
            "content": prompt
        })
    req = {
        "model": {
            "name": "chatglm2-pro",
        },
        "parameters": {
            "max_new_tokens": 128,  # 输出文本的最大tokens限制
            "temperature": 0,  # 用于控制生成文本的随机性和创造性，Temperature值越大随机性越大，取值范围0~1
            "top_p": 0.8,  # 用于控制输出tokens的多样性，TopP值越大输出的tokens类型越丰富，取值范围0~1
            "top_k": 16,  # 选择预测值最大的k个token进行采样，取值范围0-1024，0表示不生效
        },
        "messages": conversations
    }

    try:
        resps = maas.stream_chat(req)
        print("in stream: ", resps)
        res = []
        for resp in resps:
            # print(resp)
            con = resp.choice.message.content
            # print(con, end='')
            if con:
                yield con
        # print()

    except MaasException as e:
        print('glm报错啦啦啦啦啦啦啦!!!!!!!!!!!')
    except TimeoutError:
        print("glm请求超时")
    yield ""

def glm_stream(prompt, querys, answers):
    zhipu_api_key = get_zhipu_key()
    client = ZhipuAI(api_key=zhipu_api_key) # 请填写您自己的APIKey

    conversations = []
    for i in range(len(querys)):
        conversations.append({
                "role": ChatRole.USER,
                "content": querys[i]
            })
        conversations.append({
                "role": ChatRole.ASSISTANT,
                "content": answers[i]
            })
    conversations.append({
            "role": ChatRole.USER,
            "content": prompt
        })
    
    response = client.chat.completions.create(
        model="glm-3-turbo",  # 填写需要调用的模型名称
        messages=conversations,
        stream=True,
    )
    for resp in response:
        yield resp.choices[0].delta.content

# 一次返回GLM-api结果
def test_chat(maas, prompt, querys="", answers=""):
    # print(f'正在进行第{len(querys)}轮对话:')
    # print('-'*10)
    # print(prompt)
    conversations = []
    for i in range(len(querys)):
        conversations.append({
                "role": ChatRole.USER,
                "content": querys[i]
            })
        conversations.append({
                "role": ChatRole.ASSISTANT,
                "content": answers[i]
            })
    conversations.append({
            "role": ChatRole.USER,
            "content": prompt
        })
    req = {
        "model": {
            "name": "chatglm2-pro",
        },
        "parameters": {
            "max_new_tokens": 128,  # 输出文本的最大tokens限制
            "temperature": 0,  # 用于控制生成文本的随机性和创造性，Temperature值越大随机性越大，取值范围0~1
            "top_p": 0.8,  # 用于控制输出tokens的多样性，TopP值越大输出的tokens类型越丰富，取值范围0~1
            "top_k": 16,  # 选择预测值最大的k个token进行采样，取值范围0-1024，0表示不生效
        },
        "messages": conversations
    }

    try:
        resps = maas.chat(req)
        return resps.choice.message.content

    except MaasException as e:
        print('glm报错啦啦啦啦啦啦啦!!!!!!!!!!!')
    except TimeoutError:
        print("glm请求超时")

def glm_once(prompt, querys="", answers=""):
    zhipu_api_key = get_zhipu_key()
    client = ZhipuAI(api_key=zhipu_api_key) # 填写您自己的APIKey

    conversations = []
    for i in range(len(querys)):
        conversations.append({
                "role": "user",
                "content": querys[i]
            })
        conversations.append({
                "role": "assistant",
                "content": answers[i]
            })
    conversations.append({
            "role": "user",
            "content": prompt
        })
    
    response = client.chat.completions.create(
        model="glm-3-turbo", # 填写需要调用的模型名称
        messages=conversations,
    )
    return response.choices[0].message.content
# # 重新生成问题
# def test_chat(maas, prompt, querys="", answers=""):
#     # print(f'正在进行第{len(querys)}轮对话:')
#     # print('-'*10)
#     # print(prompt)
#     conversations = []
#     # "如下是一段示例：\n\n\n用户：天和核心舱多重\n助手：天和核心舱重量22.5吨。\n用户：那它搭载什么火箭升空\n 请根据以上对话将最后一个问题重写为清晰、简洁的搜索查询格式\n回答：天和核心舱搭载什么火箭升空?\n\n\n" + sentence + '用户：' + query + '\n' + '请根据以上对话将最后一个问题重写为清晰、简洁的搜索查询格式\n回答：'
#     for i in range(len(querys)):
#         conversations.append({
#                 "role": ChatRole.USER,
#                 "content": "天和核心舱多重"
#             })
#         conversations.append({
#                 "role": ChatRole.ASSISTANT,
#                 "content": "天和核心舱重量22.5吨。"
#             })
#         conversations.append({
#                 "role": ChatRole.USER,
#                 "content": "那它搭载什么火箭升空"
#             })
#         conversations.append({
#                 "role": ChatRole.ASSISTANT,
#                 "content": "天和核心舱重量22.5吨。"
#             })
#     conversations.append({
#             "role": ChatRole.USER,
#             "content": prompt
#         })
#     req = {
#         "model": {
#             "name": "chatglm2-pro",
#         },
#         "parameters": {
#             "max_new_tokens": 128,  # 输出文本的最大tokens限制
#             "temperature": 0,  # 用于控制生成文本的随机性和创造性，Temperature值越大随机性越大，取值范围0~1
#             "top_p": 0.8,  # 用于控制输出tokens的多样性，TopP值越大输出的tokens类型越丰富，取值范围0~1
#             "top_k": 16,  # 选择预测值最大的k个token进行采样，取值范围0-1024，0表示不生效
#         },
#         "messages": conversations
#     }

#     try:
#         resps = maas.chat(req)
#         return resps.choice.message.content

#     except MaasException as e:
#         print('glm报错啦啦啦啦啦啦啦!!!!!!!!!!!')
#     except TimeoutError:
#         print("glm请求超时")

# def extract_keyword(query):
#     # 使用本地加载的模型提取关键词
#     keywords = extract_kws_zh(query, kw_model)
#     max_score_keyword = max(keywords, key=lambda x: x[1])[0]

#     return max_score_keyword

# def extract_chinese_keywords(text):
#     # 使用jieba进行分词和词性标注
#     words = pseg.cut(text)
#     # 提取专有名词
#     keywords = [word for word, flag in words if flag.startswith('n') and len(word) > 1]
    
#     return keywords
    
def answer_query(query: str):
    # 用户提问
    # query='你们实验室有哪些关键技术'
    
    # 基本信息
    history_q = ['你是哈工大研发的一个机器人展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。']
    history_a = ["我知道，不论说咱们实验室还是咱们所，我知道指的都是咱工大的机器人实验室。我有丰富的机器人相关的知识。"]

    # time1 = datetime.now()
    # # 用户意图理解，改写为搜索引擎可搜索的短语
    # answer = test_stream_chat(maas, f'请看问题:“{query}”。请改写为用于搜索引擎搜索的短语并返回，不要任何修饰：', history_q, history_a)
    # # answer = test_chat(maas, f'请看问题:“{query}”。请改写为用于搜索引擎搜索的短语并返回，不要任何修饰：', history_q, history_a)

    # key_word = []
    # for an in answer:
    #     key_word.append(an)
    # key_word = "".join(key_word)
    # print("改写为搜索引擎可搜索的短语:", key_word)
    # print("test_chat cost", datetime.now() - time1)

    
    # 获取历史对话
    time1 = datetime.now()
    # history_question, history_answer = redis_getall_history(conv_handle)
    history_question = []
    if len(history_question) >= 2:
        print("历史对话超过了两轮，只需要最近的两轮")
        history_question = history_question[-2:]
        history_answer = history_answer[-2:]
    time2 = datetime.now()
    print("get history cost time = ", time2-time1)

    # if stop_detect(speak=False): return False  # 检查是否中途退出
    
    if len(history_question) > 0:
        time1 = datetime.now()
        # 用户意图理解，只用小模型和历史对话，改写为可检索的短语 并检索文档
        # 特别致谢来自xinyu的prompt：
        # "如下是一段示例：\n\n\n用户：今天几号\n助手：今天是2023年12月19日。\n用户：明天呢\n 请根据以上对话将最后一个问题重写为清晰、简洁的搜索查询格式\n回答：明天是几号?\n\n\n" + sentence + '用户：' + query + '\n' + '请根据以上对话将最后一个问题重写为清晰、简洁的搜索查询格式\n回答：'
        history_q_re = ['介绍一下火星车']
        history_a_re = ["火星探测车是指在火星登陆用于火星探测的可移动探测器，是人类发射的在火星表面行驶并进行考察的一种车辆。火星车之前由美国和前苏联多次发射。火星车传来了大量的火星资料，为人类了解火星做出了巨大的贡献。"]
        history_q_re.append("那他的贡献有哪些\n请根据以上对话将最后一个问题重写为清晰、简洁的搜索查询格式\n回答：")
        history_a_re.append("那火星车的贡献有哪些?")
        history_q_re.append(history_question[-1])
        history_a_re.append(history_answer[-1])

        prompt = query + '\n' + '请根据以上对话将最后一个问题重写为清晰、简洁的搜索查询格式\n回答：'

        query = glm_once(prompt, history_q_re, history_a_re)

        print("------------\nnew query: ", query)
        time2 = datetime.now()
        print("regenerate question cost time = ", time2-time1)

    # if stop_detect(speak=False): return False  # 检查是否中途退出
    
    # 抽取关键词
    # time1 = datetime.now()
    # try:
    #     key_word = extract_keyword(query)
    # except:
    #     key_word = query
    #     print("extract_keyword wrong")
    #     pass
    # print("------------\nkey word: ", key_word)
    # time2 = datetime.now()
    # print("extract_keyword cost time = ", time2-time1)

    # if stop_detect(speak=False): return False  # 检查是否中途退出

    # bge匹配 关键词短语，不再是用query去匹配
    time1 = datetime.now()
    text1, text2, keyscore, docscore = get_bge_query(query)
    print(f"key score = {keyscore}")
    print(f"doc score = {docscore}")
    time2 = datetime.now()
    print("bge matching cost time = ", time2-time1)
    # if stop_detect(speak=False): return False  # 检查是否中途退出


    # # bing搜索，目前使用的是serpapi服务提供商
    # time1 = datetime.now()

    # try:
    #     if keyscore < 0.9 and docscore < 0.9:
    #         bing_res = bing_test(key_word)
    #         # 填写prompt
    #         prompt = f"请参考文本1:“{text1}”\n\n请参考文本2:“{text2}”\n\n请参考搜索引擎返回结果:“{bing_res}”\n\n回答问题:“{query}”\n\n将答案凝练到100字以内:"
    #         if text1 == text2:
    #             prompt = f"请参考文本:“{text1}”\n\n请参考搜索引擎返回结果:“{bing_res}”\n\n回答问题:“{query}”\n\n将答案凝练到100字以内:"
    #     else:
    #         raise
    # except Exception as e:
    #     # if "serpapi returned 400" in e.args[0]:
    #     print("Bing api error: ", e)
    #     prompt = f"请参考文本1:“{text1}”\n\n请参考文本2:“{text2}”\n\n回答问题:“{query}”\n\n将答案凝练到100字以内:"
    #     if text1 == text2:
    #         prompt = f"请参考文本:“{text1}”\n\n回答问题:“{query}”\n\n将答案凝练到100字以内:"
    # time2 = datetime.now()
    # print("bing cost time = ", time2-time1)
    
    # 不用bing
    # if keyscore < 0.9 and docscore < 0.9:
    #     return"很抱歉，您问的问题我暂时无法回答。"
    
    # 与 system prompt 拼接起来
    for i in range(len(history_question)):
        history_q.append(history_question[i])
        history_a.append(history_answer[i])

    # print history and prompt
    for i in range(len(history_a)):
        print("q: ", history_q[i])
        print("a: ", history_a[i])

    prompt = f"请参考文本1:“{text1}”\n\n请参考文本2:“{text2}”\n\n回答问题:“{query}”\n\n将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"
    if text1 == text2:
        prompt = f"请参考文本:“{text1}”\n\n回答问题:“{query}”\n\n将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"

    print("------------\n", prompt)

    # if stop_detect(speak=False): return False  # 检查是否中途退出

    # 返回res
    res = glm_once(prompt, history_q, history_a)
    return res

    

if '__main__'==__name__:
    # res = select_most_sim_exhibit("服务展区")
    # print(res)
    res = answer_query("看看服务展区")
    print(res)
    # for i in answer_query('介绍一下天宫2号'):
    #     print(i, sep="")
        # print('--')
    # query = "四足机器人呢"
    # key_word = extract_keyword(query)
    # print(key_word)
    # key_word = extract_chinese_keywords(query)
    # print(key_word)
