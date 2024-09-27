"""
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
# 导入 Langchain 的 ConversationBufferMemory 类，用于存储和管理会话记忆。
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, \
    MessagesPlaceholder
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredFileLoader
from datetime import datetime

def get_zhipu_key():
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    zhipu_api_key = config['zhipu_apikey']
    return zhipu_api_key

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

def pretty_print_docs(docs):
    print(f"\n{'-' * 100}\n".join([f"Document {i + 1}:  " + d.page_content for i, d in enumerate(docs)]))

embeddings = OpenAIEmbeddings(openai_api_key="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")
loader = UnstructuredFileLoader("/home/robot/catkin_zt/src/ros2_zt/ros2_zt/txt/航天馆展品介绍.txt")
data = loader.load()
# 文本切分
splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=4, separator="。")
texts = splitter.split_documents(data)
retriever = Chroma.from_documents(texts, OpenAIEmbeddings(openai_api_key="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")).as_retriever()
embeddings_filter = EmbeddingsFilter(embeddings=OpenAIEmbeddings(openai_api_key="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"), similarity_threshold=0.76)
# 初始化加载器 构建本地知识向量库
db1 = Chroma.from_documents(texts, embeddings,persist_directory="./chroma/news_test1")
loader = UnstructuredFileLoader("/home/robot/catkin_zt/src/ros2_zt/ros2_zt/txt/航天馆中文讲稿.txt")
data = loader.load()
# 文本切分
splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=4, separator="。")
texts = splitter.split_documents(data)
retriever = Chroma.from_documents(texts, OpenAIEmbeddings(openai_api_key="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")).as_retriever()
embeddings_filter = EmbeddingsFilter(embeddings=OpenAIEmbeddings(openai_api_key="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"), similarity_threshold=0.76)
db2 = Chroma.from_documents(texts, embeddings,persist_directory="./chroma/news_test2")
# state = 'huozi'
state = 'chatglm'
# state = 'chatgpt4'
zhipu_api_key = get_zhipu_key()
if state == 'huozi':
    username = "陈一帆"
    password_path = "/home/robot/catkin_zt/src/ros2_zt/ros2_zt/password.txt"
    builder = OpenAiBuilder("https://huozi.8wss.com")
    builder.login(username, password_path=password_path)
    client = builder.build()
    # 使用会话链处理第一个问题，并打印回应。
    query = input("请输入问题：")
    print(query)
    time3 = datetime.now()
    found_docs = db1.similarity_search_with_score(query)
    document, score = found_docs[0]
    if score > 0.2:
        summary_prompt = document.page_content
    else:
        similarDocs = db2.similarity_search(query, k=1)
        summary_prompt = "".join([doc.page_content for doc in similarDocs])
    time4 = datetime.now()
    print(f"\nScore: {score}")
    print(summary_prompt)
    chat_history = []
    time5 = datetime.now()
    messages = [
    {"role": "系统",
        "content": "你是哈工大研发的一个机器人展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。"},
    ]
    messages.append({"role": "用户",
    "content": f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"})
    print(messages)
    completion = client.chat.completions.create(
    model="huozi",
    messages=messages,
    stop=["<|endofutterance|>"],
    temperature=0.1
    )
    time6 = datetime.now()
    print("Chat response:", completion.choices[0].message.content)
    print("similar txt finding cost time = ", time4 - time3)
    print("answer cost time = ", time6 - time5)
    chat_history = completion.choices[0].message.content
    messages.append({"role": "助手", "content": chat_history})
    while True:
        # 使用会话链处理第一个问题，并打印回应。
        query = input("请输入问题：")
        print(query)
        time3 = datetime.now()
        found_docs = db1.similarity_search_with_score(query)
        document, score = found_docs[0]
        if score > 0.2:
            summary_prompt = document.page_content
        else:
            similarDocs = db2.similarity_search(query, k=1)
            summary_prompt = "".join([doc.page_content for doc in similarDocs])
        time4 = datetime.now()
        print(summary_prompt)
        print(f"\nScore: {score}")
        chat_history = []
        time5 = datetime.now()
        messages.append({"role": "用户",
                            "content": f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"})
        print(messages)
        completion = client.chat.completions.create(
            model="huozi",
            messages=messages,
            stop=["<|endofutterance|>"],
        )
        time6 = datetime.now()
        print("Chat response:", completion.choices[0].message.content)
        print("similar txt finding cost time = ", time4 - time3)
        print("answer cost time = ", time6 - time5)
        chat_history = completion.choices[0].message.content
        messages.append({"role": "助手", "content": chat_history})
elif state == 'chatglm':
    llm = ChatZhipuAI(
        model="chatglm_turbo",
        api_key=zhipu_api_key,
        temperature=0.1
    )
    # 创建聊天提示模板，包含一个系统消息、一个聊天历史占位符和一个人类消息模板。
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "你是哈工大研发的一个机器人展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )
    # 创建一个会话记忆，用于存储和返回会话中的消息。
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    # 创建一个 LLMChain 实例，包括语言模型、提示、详细模式和会话记忆。
    conversation = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=False,
        memory=memory,
    )
    while True:
        # 使用会话链处理第一个问题，并打印回应。
        query = input("请输入问题：")
        chat_history = str(memory.load_memory_variables({}))
        query = chat_history + '\n' + query + "\n根据历史对话，补全最后一个问题中缺少的名词，重写为清晰、简洁的搜索查询格式。\n"
        time1 = datetime.now()
        query = llm.predict(query)
        time2 = datetime.now()
        print(query)
        time3 = datetime.now()
        found_docs = db1.similarity_search_with_score(query)
        document, score = found_docs[0]
        if score > 0.6:
            summary_prompt = document.page_content
        else:
            similarDocs = db2.similarity_search(query, k=1)
            summary_prompt = "".join([doc.page_content for doc in similarDocs])
        print(f"\nScore: {score}")
        print(summary_prompt)
        time4 = datetime.now()
        time5 = datetime.now()
        query = f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"
        response = conversation({"question": query})
        time6 = datetime.now()
        print(response)
        # print("reform query cost time = ", time2-time1)
        print("similar txt finding cost time = ", time4 - time3)
        print("answer cost time = ", time6 - time5)

elif state == 'chatgpt4':
    llm = ChatOpenAI(openai_api_key="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", temperature=0.1)
    # 创建聊天提示模板，包含一个系统消息、一个聊天历史占位符和一个人类消息模板。
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "你是哈工大研发的一个机器人展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )
    # 创建一个会话记忆，用于存储和返回会话中的消息。
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    # 创建一个 LLMChain 实例，包括语言模型、提示、详细模式和会话记忆。
    conversation = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=False,
        memory=memory,
    )
    while True:
        # 使用会话链处理第一个问题，并打印回应。
        query = input("请输入问题：")
        chat_history = str(memory.load_memory_variables({}))
        query = chat_history + '\n' + query + "\n根据历史对话，补全最后一个问题中缺少的名词，重写为清晰、简洁的搜索查询格式。\n"
        print(query)
        time1 = datetime.now()
        query = llm.predict(query)
        time2 = datetime.now()
        print(query)
        time3 = datetime.now()
        found_docs = db1.similarity_search_with_score(query)
        document, score = found_docs[0]
        if score > 0.6:
            summary_prompt = document.page_content
        else:
            similarDocs = db2.similarity_search(query, k=1)
            summary_prompt = "".join([doc.page_content for doc in similarDocs])
        print(f"\nScore: {score}")
        print(summary_prompt)
        time4 = datetime.now()
        time5 = datetime.now()
        query = f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:"
        response = conversation({"question": query})
        time6 = datetime.now()
        print(response)
        # print("reform query cost time = ", time2-time1)
        print("similar txt finding cost time = ", time4 - time3)
        print("answer cost time = ", time6 - time5)
