# testspark.py
import json
from typing import Generator
import queue
import threading
from sparkai.llm.llm import ChatSparkLLM
from sparkai.core.messages import ChatMessage
from sparkai.core.callbacks import BaseCallbackHandler

class _SparkSingleton:
    _instance = None
    
    def __new__(cls, config_path: str = None):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_model(config_path)
        return cls._instance
    
    def _init_model(self, config_path):
        """ 初始化模型配置 """

        config_path = '/home/niic/RX/voice_pkg/scripts/config_dt.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        self.app_id = config['spark_app_id']
        print(self.app_id)
        self.api_key = config['spark_api_key']
        print(self.api_key)
        self.api_secret = config['spark_api_secret']
        print(self.api_secret)


        # if config_path:
        #     with open(config_path, 'r') as f:
        #         config = json.load(f)
        #     self.app_id = config['spark_app_id']
        #     self.api_key = config['spark_api_key']
        #     self.api_secret = config['spark_api_secret']
        # else:  # 默认测试配置
        #     self.app_id = "4c151c9f"
        #     self.api_key = "1fca7b217ca55ca4db4cde06e229a198"
        #     self.api_secret = "OGU4NGJiOTNkNTA3MzVlYTFlZDdmN2Mx"
        
        # 固定参数
        self.spark_url = "wss://spark-api.xf-yun.com/v4.0/chat"
        self.domain = "4.0Ultra"

    def _build_client(self, streaming=False):
        return ChatSparkLLM(
            spark_api_url=self.spark_url,
            spark_app_id=self.app_id,
            spark_api_key=self.api_key,
            spark_api_secret=self.api_secret,
            spark_llm_domain=self.domain,
            streaming=streaming
        )

# ======================== 流式回调处理器 ========================
class _StreamHandler(BaseCallbackHandler):
    def __init__(self):
        self.queue = queue.Queue()
        self.finished = threading.Event()
    
    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put(token)
    
    def on_llm_end(self, response, **kwargs):
        self.finished.set()

# ======================== 模块级函数 ========================
def spark_direct(system_prompt: str, query: str, config_path: str = None) -> str:
    """
    同步调用入口函数
    :param config_path: 可选配置文件路径
    """
    model = _SparkSingleton(config_path)
    try:
        client = model._build_client(streaming=False)
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=query)
        ]
        response = client.generate([messages])
        return response.generations[0][0].text if response.generations else ""
    except Exception as e:
        print(f"[Direct Error] {str(e)}")
        return ""

def spark_stream(system_prompt: str, query: str, config_path: str = None) -> Generator[str, None, None]:
    """
    流式调用入口函数
    :param config_path: 可选配置文件路径 
    """
    model = _SparkSingleton(config_path)
    handler = _StreamHandler()
    try:
        client = model._build_client(streaming=True)
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=query)
        ]
        
        def _generate():
            client.generate([messages], callbacks=[handler])
            handler.finished.set()
        
        threading.Thread(target=_generate).start()
        
        while not handler.finished.is_set() or not handler.queue.empty():
            try:
                yield handler.queue.get_nowait()
            except queue.Empty:
                continue
    except Exception as e:
        print(f"[Stream Error] {str(e)}")
    finally:
        handler.finished.set()