import time
import aiohttp
import asyncio

async def fetch_url(url):
  for i in range(10):
    time.sleep(1)
    return i
  
async def main():
    url = "http://example.com"
    content = await fetch_url(url)
    print('jojo')
    print(content)

# 运行异步主函数
asyncio.run(main())
