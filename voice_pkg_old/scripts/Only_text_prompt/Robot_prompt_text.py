# =====================================
# Author: lhkong
# Quote: Used by hsong
# 大模型，给定文本，输出匹配的预定义的动作
# =====================================
import openai
import re
import argparse
import math
import numpy as np
import os
import json
import time

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="/home/kuavo/catkin_dt/src/voice_pkg/scripts/Only_text_prompt/usr_prompt.txt")
parser.add_argument("--sysprompt", type=str, default="/home/kuavo/catkin_dt/src/voice_pkg/scripts/Only_text_prompt/sys_prompt.txt")
args = parser.parse_args()

with open("/home/kuavo/catkin_dt/config_dt.json", "r") as f:
    config = json.load(f)


print("正在初始化ChatGPT……")
openai.api_key = config["OPENAI_API_KEY_lhkong"]
openai.api_base = "https://api.xty.app/v1"  # 加速路径

with open(args.sysprompt, "r", encoding='utf-8') as f:
    sysprompt = f.read()
with open(args.prompt, "r", encoding='utf-8') as f:
    prompt = f.read()

chat_history = [
    {
        "role": "system",
        "content": sysprompt
    },
    {
        "role": "user",
        "content": "向游客挥手欢迎"
    },
    {
        "role": "assistant",
        "content": """"```python
(具体的Python代码内容)
```

这段代码使用了`XXXX`函数使得机器人来到一个接近游客的位置，`XXXX`函数使得机器人保持X和Y坐标不动并转向游客，随后使用代码`XXXX`来抬起机器人的手臂，最后使用`XXXX`函数完成挥手的动作。"""
    }
]


def ask(query):
    chat_history.append(
        {
            "role": "user",
            "content": prompt + '\n现在输入：' + query,
        }
    )
    completion = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",     # 选择模型为gpt4
        messages=chat_history,
        temperature=0
    )
    chat_history.append(
        {
            "role": "assistant",
            "content": completion.choices[0].message.content,
        }
    )
    return chat_history[-1]["content"]


# print(f"Done.")

# code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

# 找到用3个反引号包含的python代码块
def extract_python_code(content):
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)

        if full_code.startswith("python"):
            full_code = full_code[7:]

        return full_code
    else:
        return None

# 此处为初始化机器人或仿真环境的代码


# print("欢迎使用航天馆导览机器人！我随时为您提供关于机器人指令的帮助。")

# while True:
#     question = input("Robot> ")

#     if question == "退出":
#         break

#     if question == "清空":
#         os.system("cls")
#         continue

#     response = ask(question)

#     print(f"\n{response}\n")

#     code = extract_python_code(response)
#     if code is not None:
#         print("我正在运行命令，请等待……")
#         exec(extract_python_code(response))    # 这是执行项
#         print("完成！\n")


"""调用示例
from Only_text_prompt import ask
response = ask(question)
action, id = response.split(":")[1], response.split(":")[0]
"""