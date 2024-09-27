

from openai import OpenAI


def gpt(model:str, text:str):
    open_api_key = "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"
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


userword = "我想看看东方红"
exhibition = ['卫星展厅', '火箭展厅', '原地不动', '下个地点']
fewshot = {
    "请带我看看东方红吧":"卫星展厅+请带我看看东方红吧",
    "给我介绍一下火箭展厅":"火箭展厅+给我介绍一下火箭展厅",
    "带我继续参观吧":"下个地点+带我继续参观吧",
    "我没什么想问的了":"下个地点+我没什么想问的了",
    "我不想听/看了":"原地不动+我不想听/看了",
    "你好":"原地不动+你好",
    "刚刚说的火箭叫什么名字":"原地不动+刚刚说的火箭叫什么名字",
    "哈工大博物馆成立于什么时候":"原地不动+哈工大航天馆成立于什么时候？",
    "他攻炸韩国网成立于什么时候":"原地不动+哈工大航天馆成立于什么时候？",
}
fewshotstr = ""
for k, v in fewshot.items():
    fewshotstr += "听到：" + k + "\n回复：" + v + "\n\n"

prompt = f"""
你是一个哈尔滨工业大学航天馆的讲解员，现在你听到了用户说的一句话。

这句话可能是他对你说的第一句，也可能是你们交流过程中说的话。

请根据你的身份将用户说的这句话改写更加合理，并选择一个地点

您可以选择的地点有：{str(exhibition)}

回复的格式：地点+改写后的结果

一些例子：

{fewshotstr}

现在你听到：{userword}
回复：
"""
print(prompt)
res = gpt(model='gpt-4', text=prompt)
print(res)