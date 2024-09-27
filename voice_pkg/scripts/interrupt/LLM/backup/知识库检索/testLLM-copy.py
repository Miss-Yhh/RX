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

import os
#"""openai.APIConnectionError: Connection error"""
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"
#"""openai.APIConnectionError: Connection error"""

import io
import yaml
import json
import httpx
from typing import Any
from hashlib import sha256
import sentence_transformers
from openai import OpenAI, AsyncOpenAI
from langchain.retrievers import ContextualCompressionRetriever
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.retrievers.document_compressors import EmbeddingsFilter, LLMChainExtractor
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import UnstructuredFileLoader
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever


from .testgpt4 import gpt
from .testglm import glm_stream

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

def gpt(model:str, text:str):
    open_api_key = get_gpt4_key()
    client = OpenAI(api_key=open_api_key)

    # send a ChatCompletion request to count to 100
    response = client.chat.completions.create(
        model=model,  # 'gpt-3.5-turbo' 'gpt-4'
        messages=[
            {'role': 'user', 'content': text}
        ],
        temperature=0,
        stream=True  # again, we set stream=True
    )
    for chunk in response:
        yield chunk.choices[0].delta.content  # extract the message)


def construct_knowledge_base():
    debug_bool = if_debug()

    openai_api_key = get_gpt4_key()
    embeddings = HuggingFaceEmbeddings(model_name='/home/kuavo/catkin_dt/src/checkpoints/text2vec-base-chinese/snapshots/4aedd18edec668a8e716d95eda081aba8151ffd3')
    # 知识库中单段文本长度
    CHUNK_SIZE = 200
    # 知识库中相邻文本重合长度
    OVERLAP_SIZE = 10
    # 文档 1 的处理
    # 检查是否已存在嵌入向量数据库
    db1_persist_dir = "/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/chroma/news_test1"
    if not os.path.exists(db1_persist_dir):
        loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/航天馆展品介绍.txt")
        data = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=OVERLAP_SIZE
        )
        texts = splitter.split_documents(data)
        db1 = Chroma.from_documents(texts, embeddings, persist_directory=db1_persist_dir)
        db1.persist()
    else:
        if debug_bool:
            # 如果已经存在，可以选择加载现有数据库或者跳过
            print(f"Database for document 1 already exists at {db1_persist_dir}. Skipping embedding generation.")
        db1 = Chroma(persist_directory=db1_persist_dir, embedding_function=embeddings)  # 加载现有数据库

    # 文档 2 的处理
    # 检查是否已存在嵌入向量数据库
    db2_persist_dir = "/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/chroma/news_test2"
    if not os.path.exists(db2_persist_dir):
        loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/航天馆中文讲稿.txt")
        data = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=OVERLAP_SIZE
        )
        texts = splitter.split_documents(data)
        db2 = Chroma.from_documents(texts, embeddings, persist_directory=db2_persist_dir)
        db2.persist()
    else:
        if debug_bool:
            # 如果已经存在，可以选择加载现有数据库或者跳过
            print(f"Database for document 2 already exists at {db2_persist_dir}. Skipping embedding generation.")
        db2 = Chroma(persist_directory=db2_persist_dir, embedding_function=embeddings)  # 加载现有数据库

    # 文档 3 的处理
    # 检查是否已存在嵌入向量数据库
    db3_persist_dir = "/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/chroma/news_test3"
    if not os.path.exists(db3_persist_dir):
        loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/扩充文档.txt")
        data = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=OVERLAP_SIZE
        )
        texts = splitter.split_documents(data)
        db3 = Chroma.from_documents(texts, embeddings, persist_directory=db3_persist_dir)
        db3.persist()
    else:
        if debug_bool:
            # 如果已经存在，可以选择加载现有数据库或者跳过
            print(f"Database for document 3 already exists at {db3_persist_dir}. Skipping embedding generation.")
        db3 = Chroma(persist_directory=db3_persist_dir, embedding_function=embeddings)  # 加载现有数据库
    return db1, db2, db3

def construct_knowledge_base_bm25():
    openai_api_key = get_gpt4_key()
    # embeddings = HuggingFaceEmbeddings(model_name='C:\\Users\\Administrator\\Desktop\\m3e-base')
    embeddings = HuggingFaceEmbeddings(model_name='/home/kuavo/catkin_dt/src/checkpoints/text2vec-base-chinese/snapshots/4aedd18edec668a8e716d95eda081aba8151ffd3')
    # 知识库中单段文本长度
    CHUNK_SIZE = 100
    # 知识库中相邻文本重合长度
    OVERLAP_SIZE = 10
    # 对展区问答文档的处理
    # 检查是否已存在嵌入向量数据库
    db_persist_dir = "./chroma/news_test"
    if not os.path.exists(db_persist_dir):
        loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/展区问答文档.txt")
        data = loader.load()
        splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=CHUNK_SIZE,
            chunk_overlap=OVERLAP_SIZE
        )
        texts = splitter.split_documents(data)
        bm25_retriever = BM25Retriever.from_documents(
           texts
        )
        bm25_retriever.k = 2
        db = Chroma.from_documents(texts, embeddings, persist_directory=db_persist_dir)
        db.persist()
    else:
        # 如果已经存在，可以选择加载现有数据库或者跳过
        loader = UnstructuredFileLoader("/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/txt/展区问答文档.txt")
        data = loader.load()
        splitter = CharacterTextSplitter(
            separator="。",
            chunk_size=CHUNK_SIZE,
            chunk_overlap=OVERLAP_SIZE
        )
        texts = splitter.split_documents(data)
        bm25_retriever = BM25Retriever.from_documents(
           texts
        )
        bm25_retriever.k = 2
        print(f"Database for document already exists at {db_persist_dir}. Skipping embedding generation.")
        db = Chroma(persist_directory=db_persist_dir, embedding_function=embeddings)  # 加载现有数据库
    return db, bm25_retriever


class DocumentQAHuoZi:
    def __init__(self):
        self.debug_bool = if_debug() # 是否打印调试信息
        self.rewrite_bool = if_pronoun_rewrite() # 是否进行指代词语的替换改写
        self.stream_bool = if_stream() # 是否使用流式返回
    
        self.db1, self.db2, self.db3 = construct_knowledge_base()
        openai_api_key = get_gpt4_key()
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.1, model='gpt-4-turbo')

        username = "陈一帆"
        password_path = "/home/kuavo/catkin_dt/huozi_password.txt"
        builder = OpenAiBuilder("https://huozi.8wss.com")
        builder.login(username, password_path=password_path)
        self.client = builder.build()

        self.chat_history = []

    def find_similar_document_OLD_COST_20s(self, query):
        compressor = LLMChainExtractor.from_llm(self.llm)
        found_docs1 = self.db1.similarity_search_with_score(query)
        score1 = found_docs1[0][1]
        found_docs2 = self.db2.similarity_search_with_score(query)
        score2 = found_docs2[0][1]
        if score1 >= 200 and score2 >= 200:
            retriever3 = self.db3.as_retriever(search_type="mmr")
            found_docs3 = self.db3.similarity_search_with_score(query)
            score3 = found_docs3[0][1]
            compression_retriever3 = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=retriever3
            )
            compressed_docs3 = compression_retriever3.get_relevant_documents(
                query
            )
            document = compressed_docs3
            score = score3
        else:
            if score1 <= score2:
                retriever1 = self.db1.as_retriever(search_type="mmr")
                compression_retriever1 = ContextualCompressionRetriever(
                    base_compressor=compressor, base_retriever=retriever1
                )
                compressed_docs1 = compression_retriever1.get_relevant_documents(
                    query
                )
                document = compressed_docs1
                score = score1
            else:
                retriever2 = self.db2.as_retriever(search_type="mmr")
                compression_retriever2 = ContextualCompressionRetriever(
                    base_compressor=compressor, base_retriever=retriever2
                )
                compressed_docs2 = compression_retriever2.get_relevant_documents(
                    query
                )
                document = compressed_docs2
                score = score2
        return document, score
    
    def find_relevant_document(self, query):
        #compressor = LLMChainExtractor.from_llm(self.llm)
        #在展品介绍中检索
        found_docs1 = self.db1.similarity_search_with_score(query)
        document1, score1 = found_docs1[0]
        # 在展厅讲稿中检索
        found_docs2 = self.db2.similarity_search_with_score(query)
        document2, score2 = found_docs2[0]

        if self.debug_bool:
            print("\n从文档1找到的文料和相似度得分: \n", f"Score: {score1}\n{document1.page_content}") # 从文档找到的文料和相似度得分
            print("\n从文档2找到的文料和相似度得分: \n", f"Score: {score2}\n{document2.page_content}") # 从文档找到的文料和相似度得分

        if score1 >= 200 and score2 >= 200:
            #retriever3 = self.db3.as_retriever(search_type="mmr")
            # 在扩充文档中检索
            found_docs3 = self.db3.similarity_search_with_score(query)
            score3 = found_docs3[0][1]

            if self.debug_bool:
                print("\n从文档3找到的文料和相似度得分: \n", f"Score: {score3}\n{found_docs3}") # 从文档找到的文料和相似度得分

            score = score3
            if score >= 200:
                document = ""
            else: 
                document = found_docs3
        else:
            if score1 <= score2:
                document = document1
            else:
                document = document2

            if document:
                document = document.page_content
        return document

    def generate_response(self, query):
        # 使用gpt-4-turbo进行改写
        if self.rewrite_bool:
            task = f"根据历史对话，把用户最新提出的问题中的指代词语（例如他/它/这个XXX/你刚才说的XXX）替换为原词。例如，历史对话：“{'chat_history': [HumanMessage(content='请参考文本:“这是中国北斗导航卫星组网模型北斗卫星导航系统，简称北斗系统”。回答问题:“北斗卫星是何时发射的？”请给出问题的答案'), AIMessage(content='北斗卫星系统首批卫星于2000年发射。')]}”。最新问题：这个卫星的先进之处是什么？。你应该输出：北斗卫星的先进之处是什么。\n"
            hist = f"以下是历史对话：\n“{self.chat_history}”\n"
            query = f"以下是最新问题：“{query}”，请只输出你的改写，不要输出其他多余的内容。如果历史对话为空，就不需要改写了，直接输出最新的问题的原文。"

            refined_query = task + hist + query
            if self.debug_bool:
                print("\n大模型改写Prompt: \n", refined_query)  # 大模型改写Prompt

            refined_query = self.llm.predict(refined_query)
            if self.debug_bool:
                print("\n大模型改写后的问题: \n", refined_query)  # 大模型改写后的问题
        else:
            refined_query = query
        # 文档相关内容检索
        summary_prompt = self.find_relevant_document(query)
        # summary_prompt = ""
        # score = 300
        if self.debug_bool:
            print("\n从文档找到的文料: \n", f"{summary_prompt}")

        messages = [
            {"role": "系统", "content": "你是哈工大研发的一个航天馆展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。你知道一共有两个展厅：卫星展厅和火箭展厅。其中卫星展厅的展品包括但不限于东方红卫星、紫丁香一号卫星；火箭展厅的展品包括但不限于火箭一号、神州十五号。"},
            {"role": "用户", "content": f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:(如果根据参考文本无法给出答案，不要说什么“根据提供的文本无法回答”而是直接根据你的常识直接给出简洁的答案）"}
        ]
        if self.debug_bool:
            print("\n结合文档的提问: \n", messages)
        completion = self.client.chat.completions.create(
            model="huozi",
            messages=messages,
            temperature=0.1,
            extra_body={"stop_token_ids":[57000, 57001]}
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
import sys

class DocumentQAGPT4:
    def __init__(self, stream_bool=False, stream_model='gpt-4'):
        self.time_init_1 = datetime.now()

        self.debug_bool = if_debug() # 是否打印调试信息
        self.rewrite_bool = if_pronoun_rewrite() # 是否进行指代词语的替换改写
        self.stream_bool = stream_bool # 是否使用流式返回
        self.stream_model = stream_model

        self.db1, self.db2, self.db3 = construct_knowledge_base()
        # self.db, self.bm25_retriever = construct_knowledge_base()

        openai_api_key = get_gpt4_key()

        self.llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.1, model = 'gpt-4-turbo')
        
        self.prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    "你是哈工大研发的一个航天馆展厅介绍机器人、属于哈尔滨工业大学（简称哈工大）航天馆。你知道一共有两个展厅：卫星展厅和火箭展厅。其中卫星展厅的展品包括但不限于东方红卫星、紫丁香一号卫星；火箭展厅的展品包括但不限于火箭一号、神州十五号。"
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

        self.time_init_2 = datetime.now()

    def find_relevant_document_OLD_COST_20s(self, query):
        compressor = LLMChainExtractor.from_llm(self.llm)
        found_docs1 = self.db1.similarity_search_with_score(query)
        score1 = found_docs1[0][1]
        found_docs2 = self.db2.similarity_search_with_score(query)
        score2 = found_docs2[0][1]
        if score1 >= 200 and score2 >= 200:
            retriever3 = self.db3.as_retriever(search_type="mmr")
            found_docs3 = self.db3.similarity_search_with_score(query)
            score3 = found_docs3[0][1]
            compression_retriever3 = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=retriever3
            )
            compressed_docs3 = compression_retriever3.get_relevant_documents(
                query
            )
            document = compressed_docs3
            score = score3
        else:
            if score1 <= score2:
                retriever1 = self.db1.as_retriever(search_type="mmr")
                compression_retriever1 = ContextualCompressionRetriever(
                    base_compressor=compressor, base_retriever=retriever1
                )
                compressed_docs1 = compression_retriever1.get_relevant_documents(
                    query
                )
                document = compressed_docs1
                score = score1
            else:
                retriever2 = self.db2.as_retriever(search_type="mmr")
                compression_retriever2 = ContextualCompressionRetriever(
                    base_compressor=compressor, base_retriever=retriever2
                )
                compressed_docs2 = compression_retriever2.get_relevant_documents(
                    query
                )
                document = compressed_docs2
                score = score2
        return document, score
    
    def find_relevant_document(self, query):
        #compressor = LLMChainExtractor.from_llm(self.llm)
        #在展品介绍中检索
        found_docs1 = self.db1.similarity_search_with_score(query)
        document1, score1 = found_docs1[0]
        # 在展厅讲稿中检索
        found_docs2 = self.db2.similarity_search_with_score(query)
        document2, score2 = found_docs2[0]

        if self.debug_bool:
            print("\n从文档1找到的文料和相似度得分: \n", f"Score: {score1}\n{document1.page_content}") # 从文档找到的文料和相似度得分
            print("\n从文档2找到的文料和相似度得分: \n", f"Score: {score2}\n{document2.page_content}") # 从文档找到的文料和相似度得分

        if score1 >= 200 and score2 >= 200:
            #retriever3 = self.db3.as_retriever(search_type="mmr")
            # 在扩充文档中检索
            found_docs3 = self.db3.similarity_search_with_score(query)
            score3 = found_docs3[0][1]

            if self.debug_bool:
                print("\n从文档3找到的文料和相似度得分: \n", f"Score: {score3}\n{found_docs3}") # 从文档找到的文料和相似度得分

            score = score3
            if score >= 200:
                document = ""
            else: 
                document = found_docs3
        else:
            if score1 <= score2:
                document = document1
            else:
                document = document2

            if document:
                document = document.page_content
        return document
    
    def find_relevant_document_bm25(self, query):
        #在参考文档中检索
        chroma_retriever = self.db.as_retriever(search_kwargs={"k": 3})
        ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, chroma_retriever], weights=[0.0, 1.0]
        )
        found_docs = ensemble_retriever.get_relevant_documents(query)
        print(found_docs)
        # document = found_docs[0]

        document = found_docs
        return document

    def generate_response(self, summary_prompt, query):
        question = f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:(如果根据参考文本无法给出答案，不要说什么“根据提供的文本无法回答”而是直接根据你的常识直接给出简洁的答案）"
        return self.conversation({"question": question})

    def process_query(self, query):
        self.time_init_3 = datetime.now()

        chat_history = str(self.memory.load_memory_variables({}))

        if self.rewrite_bool:
            task = "根据历史对话，把用户最新提出的问题中的指代词语（例如他/它/这个XXX/你刚才说的XXX）替换为原词。例如，历史对话：“{'chat_history': [HumanMessage(content='请参考文本:“这是中国北斗导航卫星组网模型北斗卫星导航系统，简称北斗系统”。回答问题:“北斗卫星是何时发射的？”请给出问题的答案'), AIMessage(content='北斗卫星系统首批卫星于2000年发射。')]}”。最新问题：这个卫星的先进之处是什么？。你应该输出：北斗卫星的先进之处是什么。\n"
            hist = f"以下是历史对话：\n“{chat_history}”\n"
            query = f"以下是最新问题：“{query}”，请只输出你的改写，不要输出其他多余的内容。如果历史对话为空，就不需要改写了，直接输出最新的问题的原文。"

            refined_query = task + hist + query
            if self.debug_bool:
                print("\n大模型改写Prompt: \n", refined_query) # 大模型改写Prompt

            refined_query = self.llm.predict(refined_query)
            if self.debug_bool:
                print("\n大模型改写后的问题: \n", refined_query) # 大模型改写后的问题
        else: 
            refined_query = query
        
        self.time_init_4 = datetime.now()

        document = self.find_relevant_document(refined_query)
        if self.debug_bool:
            print("\n从文档找到的文料: \n", f"{document}") # 从文档找到的文料
        
        self.time_init_5 = datetime.now()

        # exit()
        
        if self.stream_bool:
            if self.debug_bool:
                print(self.time_init_2-self.time_init_1, 
                    self.time_init_4-self.time_init_3, 
                    self.time_init_5-self.time_init_4,)
                
            return self.generate_response(document, refined_query)
        else:
            response = self.generate_response(document, refined_query)
            if self.debug_bool:
                print("\n大模型生成的回答: \n", response) # 大模型根据相关文料、历史对话所生成的回答
            
            self.time_init_6 = datetime.now()

            if self.debug_bool:
                print(self.time_init_2-self.time_init_1, 
                    self.time_init_4-self.time_init_3, 
                    self.time_init_5-self.time_init_4, 
                    self.time_init_6-self.time_init_5, )

            return response['text']

    def generate_response(self, summary_prompt, query):
        question = f"请参考文本:“{summary_prompt}”回答问题:“{query}”请给出问题的答案，将答案凝练到50字以内，注意：回答不要超过50个汉字，而且回答要完整:(如果根据参考文本无法给出答案，不要说什么“根据提供的文本无法回答”而是直接根据你的常识直接给出简洁的答案）"
        if self.stream_bool:
            if self.stream_model == 'gpt-4':
                return gpt(model='gpt-4', text=question)
            elif self.stream_model == 'chatglm':
                return glm_stream(query=question)
        else:
            return self.conversation({"question": question})

def if_debug():
    return 1

def if_pronoun_rewrite():
    return 0

def if_stream():
    return 0

def search_mode():
    return 'chroma'  # old chroma bm25
    
if __name__ == '__main__':
    # doc_qa_class = DocumentQAGPT4(stream_model='gpt-4')
    doc_qa_class = DocumentQAHuoZi()

    # print(doc_qa_class.process_query("长征一号火箭曾经执行过什么任务"))
    # print(doc_qa_class.process_query("两弹一星指的是什么"))
    # print(doc_qa_class.process_query("航天员在太空中怎么睡觉"))

    # doc_qa_class.find_relevant_document("东方红一号")
    
    sys.stdin = io.open(sys.stdin.fileno(), 'r', encoding='utf8')
    sys.stdout = io.open(sys.stdout.fileno(), 'w', encoding='utf8')

    if doc_qa_class.stream_bool:
        try:
            while True:
                query = input("请输入问题：")
                for r in doc_qa_class.process_query(query):
                    if r:
                        print(r)
        except KeyboardInterrupt:
            pass
    else:
        try:
            while True:
                query = input("请输入问题：")
                print(doc_qa_class.process_query(query))
        except KeyboardInterrupt:
            pass
