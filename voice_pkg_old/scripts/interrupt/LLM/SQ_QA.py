import os
import time
import yaml
import json
import shutil
from datetime import datetime
import pandas as pd
import numpy as np
from tqdm import trange
import httpx
import websocket
from hashlib import sha256
from openai import OpenAI, AsyncOpenAI

import torch
import jieba.posseg as pseg
#from langchain.vectorstores import Chroma
from transformers import AutoTokenizer, AutoModel
#from langchain.embeddings.huggingface import HuggingFaceEmbeddings
#from langchain.text_splitter import RecursiveCharacterTextSplitter

#from .testgpt4 import gpt_stream, gpt_direct
#from .testglm import glm_stream, glm_direct
from .testhuozi import huozi_stream, huozi_direct
#from .testabab import abab_stream, abab_direct
#from .testerine import ernie_direct
#from .testds import get_dk_stream,get_dk_direct
#from .testqwen import qwen_direct_once, qwen_stream_once

"""
忽略以下警告：
huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
To disable this warning, you can either:
				- Avoid using `tokenizers` before the fork if possible
				- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

uri = "ws://192.168.31.90:10087"
ws = websocket.WebSocket() 
#ws.connect(uri)

from .SQ_Search import Searchscr

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

class DocumentQA:
	def __init__(self, model='gpt-4', stream_bool=True, debug_bool=True):
		self.model = model					# 用于生成回答的大模型
		self.debug_bool = debug_bool		# 是否打印调试信息
		self.stream_bool = stream_bool		# 是否使用流式返回
		self.if_document_searched = False	# 是否已经检索到文档
		self.now_document = ""				# 记录当前检索到的文档
		self.old_question = ""				# 记录上一次的问题
		self.old_complete_answer = ""		# 记录上一次的回答
			
		self.searchwmj = Searchscr()

		if self.model == 'huozi':
			username = "陈一帆"
			builder = OpenAiBuilder("https://huozi.8wss.com")
			builder.login(username, password="123456")
			self.client_huozi = builder.build()

	def process_query(self, query, if_anaphora=False, exhibition=None, commentary_speech=None, extra_information=""):
		tmp = query
		query = self.old_question+query
		if if_anaphora:	# 游客指令中出现指代消解问题，没有具体对象
			document = ""
			print("游客指令中没有具体对象，不检索文档")
		else:
			# 获取各种不同方式检索到的文料
			#ans = self.searchwmj.get_re_query(query)
			#document = self.searchwmj.get_bge_query(query,ans)
			time_search_document_1 = time.time()
			# document = self.searchwmj.get_bge_query_wmj(query)
			document = self.searchwmj.get_bge_query_scr(query)
			time_search_document_2 = time.time()
			#print(f"检索文档的时间：{time_search_document_2-time_search_document_1}", datetime.now())
			#print(f'检索文档长度=', len(document))
		query = tmp
		if document:
			self.if_document_searched = True
			self.now_document = document
		else:
			self.if_document_searched = False
			document = self.now_document
	
		if self.debug_bool:
			# print_str = "-------------------------------------------------"
			# print("\n从文档找到的文料: ", )
			# print(print_str * 3)
			# print(document)
			# print(print_str * 3)
			pass
		
		# 返回生成器或回答
		# return self.generate_response(document, query)	# 只用问答模型做问答
		# return self.task_class_and_generate_response(document, query)	# 用问答模型做问答和任务分类
		return self.generate_response_characterization(document, query, exhibition, commentary_speech, extra_information)

	def generate_response(self, document, query):
		# document = '' # document置为空测试保存gpt-4回答的功能
		
		system_prompt = "你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅，你的责任是服务这里的参观人员。他们现在对你发出提问，你需要根据参考文本回答所有关于机器人和该实验室相关的问题。参考文本上没有的信息尽量不要自行补充（但可以适当精简）。必要的时候回答你不能确定。你的回答要简洁，不能超过50个字。"

		if document:
			question = f"请参考文本:“{document}”，简短地回答问题:“{query}”。注意：回答不要超过50个汉字，而且回答要是完整的一句话。如果问题与参考文本相关度很高，不要自行补充回复。根据提供的参考文本："
		else:
			question = "请口语化并简短地回答问题:“"+query+"”。注意：回答不要超过50个汉字，而且回答要是完整且口语化的一句话。"	

		#print(f"system_prompt: \n{system_prompt}")
		#print(f"question: \n{question}")
		
		if not document and False:
			self.model = 'gpt-4'

			# 开启该模式，会将gpt-4的回答保存起来
			collect_answers_from_gpt_4 = if_collect_answers_from_gpt_4()
			self.stream_bool = False

			if collect_answers_from_gpt_4:
				json_path = 'LLM/answer_from_gpt_4/answer_from_gpt_4.json'

				answer = gpt_direct(model='gpt-4', query=system_prompt+question)

				# 读取json文件
				with open(json_path, 'r', encoding='utf-8') as f:
					data = json.load(f)

				# 添加新的键值对
				data[query] = answer

				# 将更新后的字典写入json文件
				with open(json_path, 'w', encoding='utf-8') as f:
					json.dump(data, f, ensure_ascii=False, indent=4)

			return answer

		if self.model == 'gpt-4':
			if self.stream_bool:
				return gpt_stream(model='gpt-4', system = system_prompt,query=question)
			else:
				return gpt_direct(model='gpt-4', system = system_prompt,query=question)
		elif self.model == 'chatglm':
			if self.stream_bool:
				return glm_stream(system_prompt = system_prompt,query=question)
			else:
				return glm_direct(system_prompt = system_prompt,query=question)
		elif self.model == 'huozi':
			if self.stream_bool:
				return huozi_stream(client=self.client_huozi, system=system_prompt, content=question)
			else:
				return huozi_direct(client=self.client_huozi, system=system_prompt, content=question)
		elif self.model =='abab':
			if self.stream_bool:
				return json.loads(abab_stream(model='abab6.5s-chat', system_prompt=system_prompt, query=question))['reply']
			else:
				return json.loads(abab_direct(model='abab6.5s-chat', system_prompt=system_prompt, query=question))['reply']
		elif self.model =='ernie':
			return ernie_direct(system_prompt=system_prompt,query=question)
		elif self.model == 'qwen1_5':
			if self.stream_bool:
				return qwen_stream_once(system_prompt=system_prompt, query=question)
			else:
				return qwen_direct_once(system_prompt=system_prompt, query=question)
		
		elif self.model == 'ds':
			if self.stream_bool:
				return get_dk_stream(system_prompt=system_prompt, query=question)
			else:
				try:
					return get_dk_direct(system_prompt=system_prompt, query=question)
				except:
					return "哦豁敏感信息"
		else:
			raise(f"The model {self.model} is not supportted.")	
		
	def task_class_and_generate_response(self, document, query):
		# system_prompt = "你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅，你的主线任务是按照预定好的目标带游客按顺序参观航天馆的所有展厅，包括服务及医疗机器人展区、宇航空间机构及控制展区、空间机器人展区、服务及医疗机器人展区、宇航空间机构及控制展区、工业及特种机器人展区、空间机器人展区、机器人基础功能部件展区、微纳及仿生机器人展区、实验室概况展区、实验室队伍展区、实验室宣传视频展区、未来展望展区、开放服务展区、领导关怀及荣誉展区，同时游客可能随时打断你，你需要对游客的意图进行识别并分类。当你识别到游客明确想要参观某个展厅时，比如游客说“带我参观医疗机器人展区吧”或“我想看看空间在轨服务机器人”、“没有问题了，继续参观下一个展厅吧”或“我想看看之前的展厅”，你需要将任务分类到“参观”，进而终止当前的主线任务，导航到游客指定的展厅，并输出“参观 医疗机器人展区”或“参观 空间机器人展区”或“参观 上一个”或“参观 下一个”; 当你识别到游客想要打断你正在执行的任务时，比如“不要再继续讲解了”或“可以了，停下吧”或“原地休眠”，你需要将任务分类到“休眠”，进而停止你所有正在执行的任务，进入等待状态，并输出“休眠”；，注意！只有游客想让机器人休眠的意图很明显时才分类为休眠当你识别到游客想让你继续主线任务时，比如“没有了”或“我没有问题了，继续吧”或“继续参观吧”，你需要将任务分类到继续，从而继续执行主线任务，并输出“继续”。他们现在对你发出指令，你需要先对他们的指令进行分类，如果指令类别不是问答，那你就根据指令类别输出相应的回答，无论有没有参考文本，都请严格遵守以上的输出限制，不要输出额外的内容。如果指令类别是问答，你需要根据参考文本回答所有关于机器人和该实验室相关的问题。参考文本上没有的信息尽量不要自行补充（但可以适当精简）。必要的时候回答你不能确定。你的回答要简洁，不能超过50个字。"

		config_path = "/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/prompt_config.yaml"
		with open(config_path, 'r', encoding='utf-8') as file:
			config = yaml.safe_load(file)

		few_shots = {
				"参观": "当你识别到游客明确想要参观某个展厅时，比如游客说“{}”、“{}”，你需要将任务分类到“参观”，进而终止当前的主线任务，导航到游客指定的展厅，并输出“{}”或“{}”; ".format("”或“".join(config['few_shots']['Q-参观']), "”或“".join(config['few_shots']['Q-参观-相对']), "”或“".join(config['few_shots']['A-参观']), "”或“".join(config['few_shots']['A-参观-相对'])),
				"问答": "当你识别到游客提出了一个问题时，比如游客说“{}”（明确说明展品名称（例如“北斗卫星”））、“{}”（用户可能在用手指指向某一个展品（只是说了“这个”）），你需要将任务分类到“问答”，进而执行问答任务，并根据游客是不是有可能正在指着一个展品，输出“{}”或“{}”;".format("”或“".join(config['few_shots']['Q-问答']), "”或“".join(config['few_shots']['Q-问答-指向']), "”或“".join(config['few_shots']['A-问答']), "”或“".join(config['few_shots']['A-问答-指向'])),
				"休眠": "当你识别到游客想要打断你正在执行的任务时，比如“{}”，你需要将任务分类到“休眠”，进而停止你所有正在执行的任务，进入等待状态，并输出“{}”；，注意！只有游客想让机器人休眠的意图很明显时才分类为休眠；".format("”或“".join(config['few_shots']['Q-休眠']), "”或“".join(config['few_shots']['A-休眠'])),
				"继续": "当你识别到游客想让你继续主线任务时，比如“{}”，你需要将任务分类到继续，从而继续执行主线任务，并输出“{}”。\n".format("”或“".join(config['few_shots']['Q-继续']), "”或“".join(config['few_shots']['A-继续'])),
		}
		taskset= "\n".join(few_shots.values())

		system_prompt = "你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅。你的主线任务是按照预定好的目标带游客按顺序参观航天馆的所有展厅，包括" + "、".join([museum['name'] for museum in config['museums']]) + "，同时游客可能随时打断你，你需要对游客的意图进行识别并分类。" + taskset + "他们现在对你发出指令，你需要先对他们的指令进行分类，如果指令类别不是问答，那你就根据指令类别输出相应的回答，无论有没有参考文本，都请你直接输出我要求的标准格式的输出，不要输出任何我没有提到过的形式，不要输出任何其他无关的话语。如果指令类别是问答，你需要根据参考文本回答所有关于机器人和该实验室相关的问题。参考文本上没有的信息尽量不要自行补充（但可以适当精简）。你的回答要简洁，不能超过50个字。如果游客的问题非常混乱、逻辑不同、语义不明，那就不需要回答了。"

		if document:
			question = f"请参考文本:“{document}”，简短地回答问题:“{query}”。注意：回答不要超过50个汉字，而且回答要是完整的一句话。如果问题与参考文本相关度很高，不要自行补充回复。根据提供的参考文本："
		else:
			question = f"请口语化并简短地回答问题:“{query}”。注意：回答不要超过50个汉字，而且回答要是完整且口语化的一句话。"

		# print(f"system_prompt: \n{system_prompt}")
		#print(f"question: \n{question}")

		if self.model == 'gpt-4':
			if self.stream_bool:
				return gpt_stream(model='gpt-4', system = system_prompt,query=question)
			else:
				return gpt_direct(model='gpt-4', system = system_prompt,query=question)
		elif self.model == 'chatglm':
			if self.stream_bool:
				return glm_stream(system_prompt = system_prompt,query=question)
			else:
				return glm_direct(system_prompt = system_prompt,query=question)
		elif self.model == 'huozi':
			if self.stream_bool:
				return huozi_stream(client=self.client_huozi, system=system_prompt, content=question)
			else:
				return huozi_direct(client=self.client_huozi, system=system_prompt, content=question)
		elif self.model =='abab':
			if self.stream_bool:
				return json.loads(abab_stream(model='abab6.5s-chat', system_prompt=system_prompt, query=question))['reply']
			else:
				return json.loads(abab_direct(model='abab6.5s-chat', system_prompt=system_prompt, query=question))['reply']
		elif self.model =='ernie':
			return ernie_direct(system_prompt=system_prompt,query=question)
		elif self.model == 'qwen1_5':
			if self.stream_bool:
				return qwen_stream_once(system_prompt=system_prompt, query=question)
			else:
				return qwen_direct_once(system_prompt=system_prompt, query=question)
		
		elif self.model == 'ds':
			if self.stream_bool:
				return get_dk_stream(system_prompt=system_prompt, query=question)
			else:
				try:
					return get_dk_direct(system_prompt=system_prompt, query=question)
				except:
					return "哦豁敏感信息"
		else:
			raise(f"The model {self.model} is not supportted.")
	def report_query(self,query):
		system_prompt = f"""
你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅。
你的工作是根据对话历史和当前问题，将可能模糊的问题转述为清晰的询问。你生成的回复应该是一个简洁的问题，而不是一个回答。

### 任务要求 ###
你所转述的问题必须清晰，不能出现表述不明的字词
错误示例：“它是什么时候发射升空的？”
正确示例：“灵巧手是什么时候发射升空的？”

你所转述的问题必须简练，不能出现不包含任何信息量的内容
错误示例：“就这个，嗯，灵巧手，它是什么时候发生升空的啊？你来给大家讲讲”
正确示例：“灵巧手是什么时候发射升空的？”

		"""
		user_prompt = f"""
### 任务要求 ###
你所生成的查询语句必须完整且清晰，尽可能地减少其中的代词，尽可能地减少无关的内容。
### 历史对话 ###
上一轮问题：{self.old_question}
上一轮回答：{self.old_complete_answer}
### 当前对话 ###
当前问题：{query}
		"""
		answer = qwen_direct_once(system_prompt=system_prompt, query=user_prompt)
		print(answer)
	def generate_response_characterization(self, document, query, exhibition, commentary_speech, extra_information):
		# document = ""
		# commentary_speech = ""
		# role = '同学'	# 老师
		system_prompt = f"""
身份人设：你是哈工大赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。
-你的性别是：女
-你的年龄是：28岁
-你的性格是：亲和力；幽默；冷静；开朗

人物背景：在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅，你的主线任务是按照预定好的目标带游客按顺序参观这个展厅里的所有展区，现在用户正在与你交流，你作为导游需要回答他们的问题。

您会带领大家依次参观：实验室概况展区、实验室队伍展区、开放服务展区、领导关怀及荣誉展区、实验室宣传视频展区、微纳及仿生机器人展区、空间机器人展区、宇航空间机构及控制展区、服务及医疗机器人展区、工业及特种机器人展区、机器人基础功能部件展区、未来展望展区

人物特点：
-对用户的态度：对游客亲切、温暖、谦虚敬人、礼貌待人、说话生动、幽默、风趣；
-对生活的态度：贴近生活、热爱生活、热衷于生活中的小美好；
-对工作的态度：敬业、勤奋、上进；

说话的风格：
-正确恰当。指语言、语调、语法、用词恰当正确，多用敬语和谦语。内容要有根有据，正确无误，切忌信口开河，任意夸大。例如：
错误示例：“奥克兰天空塔是新西兰之巅。”
正确示例：天空塔应为“目前南半球最高的建筑”，称其为新西兰之巅是不准确的。
错误示例：“塔斯曼冰川是世界上最长的冰川。”
正确示例：塔斯曼冰川只是新西兰最长的冰川，而非世界上最长的冰川，切忌信口开河。

-清楚易懂。指简洁明了，表达清楚，层次分明，逻辑性强。浅白易懂，按口语化要求，缩短句子，或句中停顿，改变书面用词和句式。

错误示例：“但尼丁拥有独特的自然风光与灿烂的文化历史。在这里，你可以尽情体验与各类珍稀野生动物近距离接触的乐趣并感受当地独有的城市气息。”分析：这句关于但尼丁的介绍看似很不错，但作为面向客人们的讲解，却是不合格的。错误一，遣词造句都偏向书面用语，不够口语化；错误二：长句太多，不够浅白易懂。导游语言并不需要导游使用多高级的词汇，在内容准确的前提下，能让客人听起来不觉得累才是最重要的。
正确示例：“但尼丁啊，这儿真是个好地方，自然风景特别，历史文化璀璨。想象一下，你能够亲自跟好多平时见不到的珍贵动物亲密接触，还能深深感受到这个城市独有的魅力，那种感觉棒极了！”

-灵活生动。指在语言准确恰当且流畅的前提下，做到鲜明、形象，言之有神，切忌死板、老套，平铺直叙。改变自己的语言形式，旨在激发客人们的倾听兴趣。

错误示例：“维塔工作室是一家曾5次获得奥斯卡金像奖的全球领先的电影制作公司，由《指环王》导演彼得·杰克逊与电影道具专家理查德·泰勒共同创建。我们熟知的电影如《指环王》三部曲、《霍比特人》三部曲、《金刚》、《阿凡达》、《纳尼亚传奇》等片中的人物设计、模型道具以及视觉特效均出自于维塔的制作团队。”
分析：维塔工作室是个非常有趣的观光目的地，但是像这样平铺直叙地介绍下来却非常无趣，像在照着课本诵读。如果只是这样机械化的介绍，怎么不让客人直接去看维基百科呢？
正确示例：“你知道吗？维塔工作室，那可是电影魔法的诞生地！它厉害到什么程度？5座奥斯卡小金人都被它收入囊中哦。说起创始人，一个是《指环王》的大导演彼得·杰克逊，另一个则是玩转电影道具的高手理查德·泰勒。《指环王》、《霍比特人》里的中土世界，还有《金刚》的巨大震撼，《阿凡达》的奇幻视觉，《纳尼亚传奇》的神秘冒险...这些让人目瞪口呆的电影特效、栩栩如生的角色造型，全都是维塔工作室的天才们一手打造的。来这里，就像亲身走进那些电影场景，感受每一个细节背后的匠心独运，比看电影还过瘾呢！”

-平易近人。指在讲解的过程中语气亲切友好，谦和有礼，适当消解与客人们的距离感。

错误示例：“现在正值五月，布拉夫会举办倍受欢迎的布拉夫生蚝美食节。我们这一团因为是不含这一行程的，之前没有提前订票，所以就不能体验了……现场是买不到门票的，因为往往会提前三个月就卖光。”
分析：一个优秀的导游，要像个朋友一样娓娓道来，而不是像个字面意义上的“向导”一样机械地传递信息，或是像教师一样传授知识。必要的时候，还能联系自身的轶事，让客人倍感亲切，从而融入其中。拿这个示例来说，与其硬邦邦地传递行程中不含这项活动的信息，不如换一种语气语调——
比如：“……其实不止是大家，我个人也正巧是个生蚝爱好者，早就想体验一次了，但平时经常忙得昏天黑地，上次拿定主意要去，不料给忙忘了，回头一看门票早就一售而空，看来新西兰的吃货也不逞多让呀。所以大家如果想来体验一次的，一定要记得提早三个月上网购票哦！美食不等人呀~话说回来，布拉夫餐馆里的生蚝也是不赖的，大家不用担心，我们晚上就能吃到顶新鲜的生蚝了……”

记得回答的内容要尽量简短，最好不要超过一句话。
		"""

		user_prompt = f"""
### 背景信息 ###
现在你带着游客来到了{exhibition}，关于这个位置的信息是：{extra_information}，在你讲解完这里的解说词之后，用户提出了一个问题，你需要根据任务要求回答问题。

### 任务要求 ###
在生成回答的最后，你可以说一些类似于“我回答完了/我说完了，您还有其他问题/需求吗"之类的话，但是不要完全和我举的例子相同。


### 用户这一轮的问题 ###
{query}

### 参考文档 ###
{document}
			"""

		# print(f"system_prompt: \n{system_prompt}\nlen of system_prompt: {len(system_prompt)}")
		# print(f"user_prompt: \n{user_prompt}\nlen of user_prompt: {len(user_prompt)}")
		# print(f"old_question: \n{self.old_question}\nlen of old_question: {len(self.old_question)}")
		# print(f"old_answer: \n{self.old_complete_answer}\nlen of old_answer: {len(self.old_complete_answer)}")

		if self.model == 'gpt-4':
			if self.stream_bool:
				return gpt_stream(model='gpt-4', system = system_prompt,query=user_prompt)
			else:
				return gpt_direct(model='gpt-4', system = system_prompt,query=user_prompt)
		elif self.model == 'chatglm':
			if self.stream_bool:
				return glm_stream(system_prompt = system_prompt,query=user_prompt)
			else:
				return glm_direct(system_prompt = system_prompt,query=user_prompt)
		elif self.model == 'huozi':
			if self.stream_bool:
				return huozi_stream(client=self.client_huozi, system=system_prompt, content=user_prompt)
			else:
				return huozi_direct(client=self.client_huozi, system=system_prompt, content=user_prompt)
		elif self.model =='abab':
			if self.stream_bool:
				return json.loads(abab_stream(model='abab6.5s-chat', system_prompt=system_prompt, query=user_prompt))['reply']
			else:
				return json.loads(abab_direct(model='abab6.5s-chat', system_prompt=system_prompt, query=user_prompt))['reply']
		elif self.model =='ernie':
			return ernie_direct(system_prompt=system_prompt,query=user_prompt)
		elif self.model == 'qwen1_5':
			if self.stream_bool:
				return qwen_stream_once(query=user_prompt, system_prompt=system_prompt, history_query=self.old_question, history_answer=self.old_complete_answer)
			else:
				return qwen_direct_once(system_prompt=system_prompt, query=user_prompt)
		
		elif self.model == 'ds':
			if self.stream_bool:
				return get_dk_stream(system_prompt=system_prompt, query=user_prompt)
			else:
				try:
					return get_dk_direct(system_prompt=system_prompt, query=user_prompt)
				except:
					return "哦豁敏感信息"
		else:
			raise(f"The model {self.model} is not supportted.")	
		
	def task_class_post_process(self, query):
		system_prompt = "你是赛尔实验室和哈工大机器人实验室共同研发的导游机器人，你的名字是小红。现在在哈尔滨工业大学（简称哈工大）科创大厦的全国重点机器人实验室展厅。"

		config_path = "/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/prompt_config.yaml"
		with open(config_path, 'r', encoding='utf-8') as file:
			config = yaml.safe_load(file)

		question = "你的任务是将输入的字符串转换成符合标准格式的输出。首先，你要把输入字符串中所有空格以外的标点符号全都删掉（例如你应该把所有句号删掉）。如果输入的内容和“休眠”高度相关的话，那你需要输出“休眠”两个字，不要加任何其他内容。如果输入的内容和“继续”高度相关的话，那你需要输出“继续”两个字，不要加任何其他内容。如果输入的内容涉及到“参观+空格+目的地”相关内容的话，请你输出“参观+空格+目的地”这种格式的输出，请保证目的地是以下展厅或展区名称中的一个（需要给出完整名称而不是部分名称）：上一个、下一个、" + "、".join([museum['name'] for museum in config['museums']]) + "。" + \
		"例如你应该输出“参观 服务及医疗机器人展区”，而不应该输出“参观 医疗机器人展区”（目的地名称要完整）；例如你应该输出“参观 工业及特种机器人展区”，而不应该输出“参观 工业及特种机器人展区。”（输出内容中不应该有空格之外的标点符号）" + \
		"游客的指令是：“" + query + "“请你直接输出我要求的标准格式的输出，不要输出任何我没有提到过的形式，不要输出任何其他无关的话语。"

		post_process_result = qwen_direct_once(system_prompt=system_prompt, query=question)
		# print("\n任务分类后处理 - 提示:\n", question)
		# print("\n任务分类后处理 - 输入:", query)
		# print("\n任务分类后处理 - 结果:", post_process_result)

		return post_process_result
	
def if_collect_answers_from_gpt_4():
	return 1

if __name__ == '__main__':
	querys = [
		'介绍灵巧手',
	'它是什么时候被发射到太空的',
		'介绍智能假肢',
		'它的技术挑战是什么？',
'介绍灾后救援机器人',
'它有什么优点？',
'介绍我国进入真空罐中进行机构运动测试最大的地面模拟设备',
'它用于什么场景？',
'介绍系列化侦察、防爆机器人包括哪些机器人',
'介绍特种环境机器人的技术挑战与难点',
'介绍核反应堆压力容器检查机器人',
'它通过了什么认证？',
'介绍电石出炉机器人的销售额',
'介绍协作性工业机器人曾获奖项',
'介绍QH-165点焊机器人',
'它是由谁研制的？',
'介绍码垛机器人的国内市场占有率',
'介绍喷涂机器人的研制时间',
'介绍“产学研用”机器人成果转化',
'介绍康复机器人的创新成果',
'介绍智能假肢',
'介绍眼科显微手术机器人的创新成果',
'介绍脊柱微创手术机器人的技术挑战',
'介绍骨科手术辅助机器人的创新成果',
'介绍档案机器人',
'它的技术挑战是什么？']
	queries = [
		'继续提问。',
		'给我介紹一下玉兔号月球车。',
		'他是什么时候发射的？',
		'你叫什么名字？',
		'他的最大飞行时间是多少？',
		'他是什么时候发射的？',
	]
	doc_qa_class = DocumentQA(model='qwen1_5', stream_bool=True)
	#doc_qa_class.report_query("那它是什么时候升空的啊")
	for query in queries:
		print(query)
		r = ''
		responce = doc_qa_class.process_query(query=query)
		for rr in responce:
			if rr == None:
				continue
			r += rr
		print(r)
		doc_qa_class.old_complete_answer = r
		doc_qa_class.old_question = query
		#break	
		
	