from openai import OpenAI

openai_api_key = "EMPTY"
openai_api_base = "http://192.168.50.14:8000/v1"

client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)

chat_response = client.chat.completions.create(
    model="huozi",
    messages=[
        {"role": "system", "content": "你是一个智能助手"},
        {"role": "user", "content": "请你用Python写一段快速排序的代码"},
    ],
    temperature=0.8,
    extra_body={"stop_token_ids": [57000, 57001]}
)

print("Chat response: ", chat_response.choices[0].message.content)

