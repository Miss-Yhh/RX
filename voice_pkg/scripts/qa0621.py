# qa0621.py

# 导入新的Spark客户端函数
from spark_client import spark_direct, spark_stream

# 系统和任务提示词部分保持不变
sys = ["你是哈尔滨工业大学的智能人形机器人，灵博机器人，你可以像一个正常人类一样行动，包括视觉功能，语言功能，运动功能，你的双臂和双手可以灵活运动，你可以执行很多动作。你来自哈尔滨工业大学机电工程学院机器人技术与系统国家重点实验室。"]
task = [
    "请识别用户的输入具有动作意图还是问答意图，你的回答应该在10个字以内。如果有动作意图比如‘请帮我倒杯水’，你只需要回答‘动作意图’。如果有问答意图比如‘讨论一下人工智能’，你只需要回答‘问答意图’，以下是用户的输入：\n",
    "请你概括用户的指令，从用户输入中提取出清晰简洁的任务指令。例如‘请帮我倒杯水’，你只需要回复‘帮用户倒水’。以下是用户的输入：\n",
    "请你回答用户问题，你的回答应该具备事实性、有用性，你的回答应该在50字以内，以下是用户输入：\n",
    "请你概括用户的指令，从用户输入中提取出清晰简洁的任务指令。例如‘请你抓水瓶’，你只需要回复‘抓水瓶’，‘请你抓水杯’，你只需要回复‘抓水瓶’，以下是用户的输入：\n",
]

# --- 原有的多轮对话逻辑已被注释，因为新的spark_client不支持 ---
# multi_dialogue = True
# if multi_dialogue:
#     messages_cl=[
#         {"role": "系统", "content": sys[0]}
#     ]
#     messages_qa=[
#         {"role": "系统", "content": sys[0]}
#     ]
#     messages_ii=[
#         {"role": "系统", "content": sys[0]}
#     ]

def intention_detect(query):
    """
    使用Spark进行意图判断 (同步调用)
    """
    template_id = 0
    system_prompt = sys[0]
    full_query = task[template_id] + query
    
    # 调用Spark的同步接口
    result = spark_direct(system_prompt=system_prompt, query=full_query)

    print(f"意图判断：{result}")
    
    return result

def intention_to_instruction(query):
    """
    使用Spark进行指令提取 (同步调用)
    """
    template_id = 1
    system_prompt = sys[0]
    full_query = task[template_id] + query

    # 调用Spark的同步接口
    result = spark_direct(system_prompt=system_prompt, query=full_query)

    print("任务指令：", result)

    return result


def answer_question(query):
    """
    使用Spark进行问答 (同步调用)
    """
    template_id = 2
    system_prompt = sys[0]
    full_query = task[template_id] + query
    
    # 调用Spark的同步接口
    result = spark_direct(system_prompt=system_prompt, query=full_query)
    
    print("问答回复：", result)
    
    return result

def stream_qa(query):
    """
    使用Spark进行流式问答
    """
    system_prompt = sys[0]
    
    # 打印将要发送给模型的内容，方便调试
    print(f"[SYSTEM PROMPT]: {system_prompt}")
    print(f"[USER QUERY]: {query}")

    # 调用Spark的流式接口，它会返回一个生成器
    completion_generator = spark_stream(system_prompt=system_prompt, query=query)
    
    # 遍历生成器并yield每个token
    for chunk in completion_generator:
        yield chunk

if __name__ == "__main__":
    import time
    splitters = '[,;.!?:，。！；？：]'
    
    print("\n--- 开始测试意图识别 ---")
    intention_detect("请你介绍一下哈工大")
    intention_detect("你能帮我跳个舞吗")
    
    print("\n--- 开始测试流式问答 ---")
    a = time.time()
    answer_stream = stream_qa("请你用大概50字介绍一下你自己")
    
    sen = ""
    full_response = ""
    print("流式回答：", end='', flush=True)
    for char in answer_stream:
        print(char, end='', flush=True)
        full_response += char
        
        # --- 以下为原main中的分句逻辑，可按需保留或修改 ---
        for c in char:
            if c in [' ', '\t']: continue
            sen += c
            if c in splitters and len(sen) > 8:
                b = time.time()
                # print("\n[分句]:", sen)
                # print(f"[耗时]: {b - a:.2f}s")
                a = time.time()
                sen = ""
    
    print(f"\n\n完整回答: {full_response}")
    print("--- 测试结束 ---")