import httpx
from hashlib import sha256
from openai import OpenAI, AsyncOpenAI

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
 
    def build_async(self) -> AsyncOpenAI:
        http_client = httpx.AsyncClient(cookies=self.cookies)
        client = AsyncOpenAI(
            base_url=f"{self.base_url}/api/v1",
            api_key="token-abc123",
            http_client=http_client
        )
        return client
    
username = "陈一帆"
builder = OpenAiBuilder("https://huozi.8wss.com")
builder.login(username, password="123456")
client = builder.build()