import openai
from openai import OpenAI

def get_lingyi_direct(system:str,content:str):
    API_BASE = "https://api.lingyiwanwu.com/v1"
    API_KEY = "25ea2fa7519f449f9c28fb71da8a5734"
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE
    )
    completion = client.chat.completions.create(
    model="yi-large",
    messages=[{'role':'system','content':system},{"role": "user", "content": content}]
    )
    print(completion.choices[0].message.content)
    return completion.choices[0].message.content
if __name__ == '__main__':
    get_lingyi_direct('你是一个智能助手','你叫什么名字？')
# from transformers import AutoModelForCausalLM, AutoTokenizer

# model_path = '01-ai/Yi-1.5-9B-chat'

# tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

# # Since transformers 4.35.0, the GPT-Q/AWQ model can be loaded using AutoModelForCausalLM.
# model = AutoModelForCausalLM.from_pretrained(
#     model_path,
#     device_map="auto",
#     torch_dtype='auto'
# ).eval()

# # Prompt content: "hi"
# messages = [
#     {"role": "user", "content": "hi"}
# ]

# input_ids = tokenizer.apply_chat_template(conversation=messages, tokenize=True, return_tensors='pt')
# output_ids = model.generate(input_ids.to('cuda'), eos_token_id=tokenizer.eos_token_id)
# print(output_ids)
# response = tokenizer.decode(output_ids[0], skip_special_tokens=True)

# # Model response: "Hello! How can I assist you today?"
# print(response)