"""
运行该文件需要安装的依赖：
pip install langchain
pip install lark==1.1.5
pip install unstructured
pip install chromadb
pip install tiktoken

cd /home/$user_name
git clone https://github.com/nltk/nltk_data.git
cd nltk_data/tokenizers
unzip punkt.zip
cd ../taggers
unzip averaged_perceptron_tagger.zip
"""

"""openai.APIConnectionError: Connection error"""
import os
os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
"""openai.APIConnectionError: Connection error"""

import json
import httpx
from hashlib import sha256
from openai import OpenAI, AsyncOpenAI
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredFileLoader

import yaml

from .testgpt4 import gpt

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
            password = sha256(password.encode('utf-8')).hexdigest()
        assert password, "password or password_path must be provided"

        login = httpx.post(f"{self.base_url}/api/login", json={"name": username, "password_hash": password})
        if login.status_code != 200:
            raise Exception(f"Failed to login: {login.text}")
        self.cookies = {key: value for key, value in login.cookies.items()}

    def build(self) -> OpenAI:
        http_client = httpx.Client(cookies=self.cookies)
        client = OpenAI(
            base_url=f"{self.base_url}/api/v1",
            api_key="token-abc123",
            http_client=http_client
        )

        return client

    def build_async(self) -> AsyncOpenAI:
        http_client = httpx.AsyncClient(cookies=self.cookies)
        client = AsyncOpenAI(
            base_url=f"{self.base_url}/api/v1",
            api_key="token-abc123",
            http_client=http_client
        )
        return client
    
def get_gpt4_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    openai_api_key = config['openai_api_key']
    return openai_api_key

def get_ghuozi_password():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    huozi_password_path = config['huozi_password_path']
    return huozi_password_path

def construct_konwladge_base():
    openai_api_key = get_gpt4_key()

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    
    # 文档 1
    loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/航天馆展品介绍.txt")
    data = loader.load()

    # 文本切分
    splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=4, separator="。")
    texts = splitter.split_documents(data)
    retriever = Chroma.from_documents(texts, OpenAIEmbeddings(openai_api_key=openai_api_key)).as_retriever()
    embeddings_filter = EmbeddingsFilter(embeddings=OpenAIEmbeddings(openai_api_key=openai_api_key), similarity_threshold=0.76)

    # 初始化加载器 构建本地知识向量库
    db1 = Chroma.from_documents(texts, embeddings, persist_directory="./chroma/news_test1")

    # 文档 2
    loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/航天馆中文讲稿.txt")
    data = loader.load()

    # 文本切分
    splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=4, separator="。")
    texts = splitter.split_documents(data)
    retriever = Chroma.from_documents(texts, OpenAIEmbeddings(openai_api_key=openai_api_key)).as_retriever()
    embeddings_filter = EmbeddingsFilter(embeddings=OpenAIEmbeddings(openai_api_key=openai_api_key), similarity_threshold=0.76)

    # 初始化加载器 构建本地知识向量库
    db2 = Chroma.from_documents(texts, embeddings, persist_directory="./chroma/news_test2")

    return db1, db2

class DocumentQAHuoZi:
    def __init__(self):
        self.db1, self.db2 = construct_konwladge_base()
        
        username = "陈一帆"
        password_path = get_ghuozi_password()
        builder = OpenAiBuilder("https://huozi.8wss.com")
        builder.login(username, password_path=password_path)
        self.client = builder.build()

        self.chat_history = []

        self.debug_bool = if_debug() # 是否打印调试信息
        self.rewrite_bool = if_pronoun_rewrite() # 是否进行指代词语的替换改写

    def find_similar_document(self, query):
        found_docs = self.db1.similarity_search_with_score(query)
        document, score = found_docs[0]
        if score > 0.2:
            summary_prompt = document.page_content
        else:
            similarDocs = self.db2.similarity_search(query, k=1)
            summary_prompt = "".join([doc.page_content for doc in similarDocs])
        return summary_prompt, score

    def generate_response(self, query):
        # 使用gpt-3.5-turbo进行改写
        if self.rewrite_bool:
            task = "根据历史对话，把用户最新提出的问题中的指代词语（例如他/它/这个XXX/你刚才说的XXX）替换为完整名词。例如，历史对话：“['北斗卫星导航系统是中国自主研发的全球卫星导航系统，由空间段、地面段和用户段组成，提供高精度、高可靠定位、导航、授时服务，并具有短报文通信能力。']”。那么你可以提炼出历史对话中的核心名词是“北斗卫星”。对于最新问题：这个卫星的先进之处是什么？。你应该输出：北斗卫星的先进之处是什么。\n"
            hist = f"以下是历史对话：\n“{self.chat_history}”\n"
            quer = f"以下是最新问题：“{query}”，请只输出你改写后的内容，不要输出其他多余的内容。如果历史对话为“[]”，就不需要改写了，直接输出最新的问题的原文。"

            refined_query = task + hist + quer
            if self.debug_bool:
                print("\n大模型改写Prompt: \n", refined_query) # 大模型改写Prompt

            reslist = gpt(model='gpt-3.5-turbo', text=refined_query)
            refined_query = ''
            for r in reslist:
                if r:
                    refined_query += str(r)
            if self.debug_bool:
                print("\n大模型改写后的问题: \n", refined_query) # 大模型改写后的问题
            
            query = refined_query
        
        # 文档相关内容检索
        summary_prompt, score = self.find_similar_document(query)
        if self.debug_bool:
            print("\n从文档找到的文料和相似度得分: \n", f"Score: {score}\n{summary_prompt}")

        messages = [
            {"role": "系统", "content": "你是哈工大研发的一个机器人展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。"},
            {"role": "用户", "content": f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"}
        ]
        if self.debug_bool:
            print("\n结合文档的提问: \n", messages)
        completion = self.client.chat.completions.create(
            model="huozi",
            messages=messages,
            stop=["<|endofutterance|>"],
            temperature=0.1
        )
        chat_response = completion.choices[0].message.content
        if self.debug_bool:
            print("\n大模型生成的回答: \n", chat_response)
        return chat_response

    def process_query(self, query):
        chat_response = self.generate_response(query)
        self.chat_history.append(chat_response)
        
        return chat_response

from datetime import datetime

class DocumentQAGPT4:
    def __init__(self):
        self.time_init_1 = datetime.now()
        self.db1, self.db2 = construct_konwladge_base()

        openai_api_key = get_gpt4_key()

        self.llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.1)
        self.prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    "你是哈工大研发的一个机器人展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。"
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.conversation = LLMChain(
            llm=self.llm,
            prompt=self.prompt,
            verbose=False,
            memory=self.memory,
        )

        self.debug_bool = if_debug() # 是否打印调试信息
        self.rewrite_bool = if_pronoun_rewrite() # 是否进行指代词语的替换改写

        self.time_init_2 = datetime.now()

    def process_query(self, query):
        self.time_init_3 = datetime.now()

        chat_history = str(self.memory.load_memory_variables({}))

        if self.rewrite_bool:
            task = "根据历史对话，把用户最新提出的问题中的指代词语（例如他/它/这个XXX/你刚才说的XXX）替换为原词。例如，历史对话：“{'chat_history': [HumanMessage(content='请参考文本:“这是中国北斗导航卫星组网模型北斗卫星导航系统，简称北斗系统”。回答问题:“北斗卫星是何时发射的？”请给出问题的答案'), AIMessage(content='北斗卫星系统首批卫星于2000年发射。')]}”。最新问题：这个卫星的先进之处是什么？。你应该输出：北斗卫星的先进之处是什么。\n"
            hist = f"以下是历史对话：\n“{chat_history}”\n"
            quer = f"以下是最新问题：“{query}”，请只输出你的改写，不要输出其他多余的内容。如果历史对话为空，就不需要改写了，直接输出最新的问题的原文。"

            refined_query = task + hist + quer
            if self.debug_bool:
                print("\n大模型改写Prompt: \n", refined_query) # 大模型改写Prompt

            refined_query = self.llm.predict(refined_query)
            if self.debug_bool:
                print("\n大模型改写后的问题: \n", refined_query) # 大模型改写后的问题
        else: 
            refined_query = query
        
        self.time_init_4 = datetime.now()
        
        document, score = self.find_relevant_document(refined_query)
        if self.debug_bool:
            print("\n从文档找到的文料和相似度得分: \n", f"Score: {score}\n{document}") # 从文档找到的文料和相似度得分
        
        self.time_init_5 = datetime.now()
        
        response = self.generate_response(document, refined_query)
        if self.debug_bool:
            print("\n大模型生成的回答: \n", response) # 大模型根据相关文料、历史对话所生成的回答
        
        self.time_init_6 = datetime.now()

        print(self.time_init_2-self.time_init_1, 
              self.time_init_4-self.time_init_3, 
              self.time_init_5-self.time_init_4, 
              self.time_init_6-self.time_init_5, )

        return response['text']

    def find_relevant_document(self, query):
        found_docs = self.db1.similarity_search_with_score(query)
        document, score = found_docs[0]
        if score <= 0.6:
            similar_docs = self.db2.similarity_search(query, k=1)
            document = "".join([doc.page_content for doc in similar_docs])
        return document, score

    def generate_response(self, summary_prompt, query):
        question = f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"
        return self.conversation({"question": question})

def if_debug():
    return 1

def if_pronoun_rewrite():
    return 0
    
if __name__ == '__main__':
    doc_qa_class = DocumentQAGPT4()
    # doc_qa_class = DocumentQAHuoZi()

    # print(doc_qa_class.process_query("你好"))

    # print(doc_qa_class.process_query("介绍一下东方红一号"))
    # print(doc_qa_class.process_query("介绍一下他的重量、长度"))
    # print(doc_qa_class.process_query("他还发射过什么卫星？"))

    while True:
        question = input("请输入你的问题：")
        doc_qa_class.process_query(question)
