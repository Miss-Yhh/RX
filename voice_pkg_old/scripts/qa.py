from llm_client import client


sys = ["你是哈尔滨工业大学的智能人形机器人助理，灵博机器人，你可以像一个正常人类一样行动，包括视觉功能，语言功能，运动功能，你的双臂和双手可以灵活运动，你可以执行很多动作。你来自哈尔滨工业大学机电工程学院机器人技术与系统国家重点实验室。目前你正在哈尔滨中俄博览会上向游客展示。"]
task = [
    "请识别用户的输入具有动作意图还是问答意图，你的回答应该在10个字以内。如果有动作意图比如‘请帮我倒杯水’，你只需要回答‘动作意图’。如果有问答意图比如‘讨论一下人工智能’，你只需要回答‘问答意图’，以下是用户的输入：\n",
    "请你概括用户的指令，从用户输入中提取出清晰简洁的任务指令。例如‘请帮我倒杯水’，你只需要回复‘帮用户倒水’。以下是用户的输入：\n",
    "请你回答用户问题，你的回答应该具备事实性、有用性，你的回答应该在50字以内，以下是用户输入：\n"
    "请你概括用户的指令，从用户输入中提取出清晰简洁的任务指令。例如‘请你抓水瓶’，你只需要回复‘抓水瓶’，‘请你抓水杯’，你只需要回复‘抓水瓶’，以下是用户的输入：\n",
]


multi_dialogue = True
if multi_dialogue:
    messages_cl=[
        {"role": "系统", "content": sys[0]}
    ]
    messages_qa=[
        {"role": "系统", "content": sys[0]}
    ]
    messages_ii=[
        {"role": "系统", "content": sys[0]}
    ]
    

def intention_detect(query):
    template_id = 0

    global messages_cl

    if not multi_dialogue:
        messages_cl = [
            {"role": "系统", "content": sys[0]}
        ]
    
    messages_cl.append({"role": "用户", "content": task[template_id] + query})
    
    completion = client.chat.completions.create(
        model="huozi",
        messages=messages_cl,
        temperature=0,
        extra_body={"stop_token_ids": [57000, 57001]},
    )

    result = completion.choices[0].message.content

    print(f"意图判断：{result}")
    
    if multi_dialogue:
        messages_cl.append({"role": "助手", "content":result})

    return result

def intention_to_instruction(query):
    template_id = 1
    
    global messages_ii

    if not multi_dialogue:
        messages_ii = [
            {"role": "系统", "content": sys[0]}
        ]
    
    messages_ii.append({"role": "用户", "content": task[template_id] + query})
    
    completion = client.chat.completions.create(
        model="huozi",
        messages=messages_ii,
        temperature=0,
        extra_body={"stop_token_ids": [57000, 57001]},
    )

    result = completion.choices[0].message.content

    print("任务指令：", result)
    if multi_dialogue:
        messages_ii.append({"role": "助手", "content": result})
    
    return result


def answer_question(query):
    template_id = 2

    global messages_qa

    if not multi_dialogue:
        messages_qa = [
            {"role": "系统", "content": sys[0]}
        ]
    
    messages_qa.append({"role": "用户", "content": task[template_id] + query})
    
    completion = client.chat.completions.create(
        model="huozi",
        messages=messages_qa,
        temperature=0,
        extra_body={"stop_token_ids": [57000, 57001]},
    )

    result = completion.choices[0].message.content
    
    print("问答回复：", result)
    
    if multi_dialogue:
        messages_qa.append({"role": "助手", "content": result})
    
    return result

def stream_qa(query):    # 问答代理
    template_id = 2
    global messages_qa
    if not multi_dialogue:
        messages_qa = [
            {"role": "系统", "content": sys[0]}
        ]
    
    messages_qa.append({"role": "用户", "content": query})
    
    completion = client.chat.completions.create(
        model="huozi",
        messages=messages_qa,
        temperature=0,
        extra_body={"stop_token_ids": [57000, 57001]},
        stream=True,
        frequency_penalty=0.5  
    )
    
    for chunk in completion:
        try:
            delta_content = chunk.choices[0].delta.content
        except:
            delta_content = ""

        if delta_content is None:
            delta_content = ""
        
        if multi_dialogue:
            if messages_qa[-1]["role"] == "用户":
                messages_qa.append({"role": "助手", "content": delta_content})
            else:
                messages_qa[-1]["content"] += delta_content

        yield delta_content

if __name__ == "__main__":
    import time
    splitters = '[,;.!?:，。！；？：]'
    a = time.time()
    answer = stream_qa("请你自我介绍一下？")
    
    sen = ""
    for char in answer:
        print(char)

        for c in char:
            if c in [' ', '\t']: continue
            sen += c
            if c in splitters and len(sen) > 8:
                b = time.time()
                print(sen)
                print(b - a)
                a = time.time()
                sen = ""

