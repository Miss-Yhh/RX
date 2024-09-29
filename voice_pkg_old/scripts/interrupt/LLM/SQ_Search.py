import os
import yaml
import json
import shutil
from datetime import datetime
import pandas as pd
import numpy as np
from tqdm import trange
import httpx
from hashlib import sha256
from openai import OpenAI, AsyncOpenAI
import time

import asyncio
import websockets
import websocket
import torch
import jieba.posseg as pseg
#from langchain.vectorstores import Chroma
from transformers import AutoTokenizer, AutoModel
#from langchain.embeddings.huggingface import HuggingFaceEmbeddings
#from langchain.text_splitter import RecursiveCharacterTextSplitter

# from .testgpt4 import gpt_stream, gpt_direct
# from .testglm import glm_stream, glm_direct
# from .testhuozi import huozi_stream, huozi_direct
# from .testabab import abab_stream, abab_direct
# from .testerine import ernie_direct
# from .testds import get_dk_stream,get_dk_direct
# from .testqwen import qwen_direct_once, qwen_stream_once
# from .testlingyi import get_lingyi_direct

"""
忽略以下警告：
huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
To disable this warning, you can either:
		- Avoid using `tokenizers` before the fork if possible
		- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

"""openai.APIConnectionError: Connection error"""
# import os
os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
"""openai.APIConnectionError: Connection error"""
uri = "ws://192.168.31.90:10087"
ws = websocket.WebSocket() 
ws.connect(uri)

# class Searchwmj:
# 	def __init__(self) -> None:
# 		keyresults0, docresults0 = self.readjson('/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/LLM/json/hh.json')
# 		keyresults1, docresults1 = self.readjson_gpt4('LLM/json/wmj.json')
# 		keyresults2, docresults2 = self.readjson_gpt4('LLM/answer_from_gpt_4/answer_from_gpt_4.json')
# 		self.jsondata = {'关键词':keyresults0+keyresults1+keyresults2, '描述内容':docresults0+docresults1+docresults2}
# 		self.tokenizer = AutoTokenizer.from_pretrained('ckptpath/bge-small-zh-v1.5')
# 		self.model = AutoModel.from_pretrained("ckptpath/bge-small-zh-v1.5")
# 		self.model.eval()
	
# 	def readjson(self, path):
# 		keyresults, docresults = [], []
# 		with open(path, 'r', encoding='utf-8') as f:
# 				data = json.load(f)
		
# 		def find_values(json_data, key, para):
# 				"""递归搜索所有键为 key 的值"""
# 				if isinstance(json_data, dict):	# 如果当前数据是字典
# 						for k, v in json_data.items():
# 								if k == key:
# 										keyresults.append(v)	# 如果找到了匹配的键，添加其值到结果列表
# 								if k == para:
# 										docresults.append(v)	# 如果找到了匹配的键，添加其值到结果列表
# 								find_values(v, key, para)	# 递归搜索该键的值
# 				elif isinstance(json_data, list):	# 如果当前数据是列表
# 						for item in json_data:
# 								find_values(item, key, para)	# 递归搜索列表中的每一个元素
# 		find_values(json_data=data, key='name', para='introduction')
# 		return keyresults, docresults
	
# 	def readjson_gpt4(self, jsonpath):
# 		with open(jsonpath, 'r') as f:
# 			data = json.load(f)
# 		keys = list(data.keys())
# 		values = list(data.values())
# 		return keys, values

# 	def manyquerykeys_in_para(self, keywords, para):
# 		count = 0
# 		for key in keywords:
# 				if key in para:
# 					count += 1
# 		return count == len(keywords)
						 
# 	def get_re_query(self, query='说说机器人是什么'):
# 		def extract_nouns(sentence):
# 				words = pseg.cut(sentence)
# 				nouns = [word.word for word in words if word.flag.startswith('n')]
# 				return nouns

# 		query_keywords = list(set(extract_nouns(query)))
# 		match_keypara = []
# 		for i in range(len(self.jsondata['关键词'])):
# 			keyword = self.jsondata['关键词'][i]
# 			para = self.jsondata['描述内容'][i]
# 			for query_keyword in query_keywords:
# 				if query_keyword in keyword or self.manyquerykeys_in_para(query_keywords, para):
# 					match_keypara.append(keyword+":"+para)
# 		match_keypara = list(set(match_keypara))
# 		if len(match_keypara) == 0:
# 			return ""
# 		else:
# 			res = ";\n\n".join(match_keypara)
# 			return res	# list

def get_query_embedding(encoded_input):

	print(encoded_input)
	encoded_input_ser = {
		"input_ids":encoded_input['input_ids'].tolist(),
		"token_type_ids":encoded_input['token_type_ids'].tolist(),
		"attention_mask":encoded_input['attention_mask'].tolist()
	}
	ws.send(json.dumps(encoded_input_ser))
	response = ws.recv()
	received_tensor = json.loads(response)
	return received_tensor

class Searchscr:
	def __init__(self) -> None:
		csv_file_path = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/qa_legacy/qa_data/documents_lecture_all-v4.csv'
		self.locs={'飞行器相关物品展示':1,'航天相关物品展示':1,'机器人相关物品展示':1,'老师个人介绍':1,'实验室相关内容':1,'专业名词解释':1,'工业及特种机器人':1,'特种机器人':1,'工业机器人':1,'宇航空间机构及控制':1,'空间机器人':1,'仿生机器人':1,'实验室研究方向':1,'实验室概述':1,'研究团队':1,'开放服务':1,'捣炉机器人系统':1, '展区介绍':1,'小型娱乐机器人':1}
		df = pd.read_csv(csv_file_path)
		column0 = df['aaa分类'].tolist()
		column1 = df['关键词'].tolist()
		column2 = df['描述内容'].tolist()
		df2=pd.read_csv("/home/kuavo/catkin_dt/src/voice_pkg/scripts/qa_legacy/qa_data/example.csv")
		column0_2 = df2['关键词'].tolist()
		column1_2 = df2['描述内容'].tolist()
		self.jsondata_2={'关键词':column0_2, '描述内容':column1_2}
		
		self.jsonalldata={'分类': column0, '关键词':column1, '描述内容':column2}
		self.jsondata={'关键词':[], '描述内容':[]}
		self.tokenizer = AutoTokenizer.from_pretrained('/home/robot/.cache/huggingface/hub/models--infgrad--stella-large-zh-v3-1792d/snapshots/d5d39eb8cd11c80a63df53314e59997074469f09')
		# self.model = AutoModel.from_pretrained("/home/robot/.cache/huggingface/hub/models--infgrad--stella-large-zh-v3-1792d/snapshots/d5d39eb8cd11c80a63df53314e59997074469f09")
		# self.model.eval()
		self.get_jsons()
#		self.bgeKeywords = self.get_bge_embedding()
		self.bgeKeywords_2 = self.get_bge_embedding_2()

	def get_jsons(self,):
		list0 = []
		list1 = []
		for i,j,k in zip(self.jsonalldata['分类'],self.jsonalldata['关键词'],self.jsonalldata['描述内容']):
			if self.locs[i]==1:
				list0.append(j)
				list1.append(k)
		self.jsondata={'关键词':list0, '描述内容':list1}

	# def get_bge_embedding(self,):
	# 	# Tokenize sentences
	# 	encoded_input = self.tokenizer(self.jsondata['关键词'], max_length=512, padding=True, truncation=True, return_tensors='pt')

	# 	# Compute token embeddings
	# 	with torch.no_grad():
	# 			model_output = self.model(**encoded_input)
	# 			# Perform pooling. In this case, cls pooling.
	# 			sentence_embeddings = model_output[0][:, 0]
	# 	# normalize embeddings
	# 	key_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

	# 	# # Tokenize sentences
	# 	# encoded_input = self.tokenizer(self.jsondata['描述内容'], max_length=512, padding=True, truncation=True, return_tensors='pt')

	# 	# # Compute token embeddings
	# 	# with torch.no_grad():
	# 	#		 model_output = self.model(**encoded_input)
	# 	#		 # Perform pooling. In this case, cls pooling.
	# 	#		 sentence_embeddings = model_output[0][:, 0]
	# 	# # normalize embeddings
	# 	# sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

	# 	# 保存embedding到numpy
	# 	return {'key':key_embeddings, 'para':sentence_embeddings}
	def get_bge_embedding_2(self):
		# Tokenize sentences
		###print("开始tokenize\n")
		encoded_input = self.tokenizer(self.jsondata_2['描述内容'], max_length=512, padding=True, truncation=True, return_tensors='pt')
		###print("tokenize完毕\n开始embedding\n")
		# Compute token embeddings
		# with torch.no_grad():
		# 		model_output = self.model(**encoded_input)
		# 		# Perform pooling. In this case, cls pooling.
		# 		sentence_embeddings = model_output[0][:, 0]
		# # normalize embeddings
		# torch.save(sentence_embeddings, '/home/kuavo/catkin_dt/src/checkpoints/sentence_embeddings.pt')
		# print('load_done')
		sentence_embeddings=torch.load('/home/kuavo/catkin_dt/src/checkpoints/sentence_embeddings.pt')
		###print("embedding完毕\n")
		key_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

		# # Tokenize sentences
		# encoded_input = self.tokenizer(self.jsondata['描述内容'], max_length=512, padding=True, truncation=True, return_tensors='pt')

		# # Compute token embeddings
		# with torch.no_grad():
		#		 model_output = self.model(**encoded_input)
		#		 # Perform pooling. In this case, cls pooling.
		#		 sentence_embeddings = model_output[0][:, 0]
		# # normalize embeddings
		# sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

		# 保存embedding到numpy
		return {'key':key_embeddings, 'para':sentence_embeddings}#TODO
	
	def readjson(self, path):
		keyresults, docresults = [], []
		with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
		
		def find_values(json_data, key, para):
				"""递归搜索所有键为 key 的值"""
				if isinstance(json_data, dict):	# 如果当前数据是字典
						for k, v in json_data.items():
								if k == key:
										keyresults.append(v)	# 如果找到了匹配的键，添加其值到结果列表
								if k == para:
										docresults.append(v)	# 如果找到了匹配的键，添加其值到结果列表
								find_values(v, key, para)	# 递归搜索该键的值
				elif isinstance(json_data, list):	# 如果当前数据是列表
						for item in json_data:
								find_values(item, key, para)	# 递归搜索列表中的每一个元素
		find_values(json_data=data, key='name', para='introduction')
		return keyresults, docresults
	
	def readjson_gpt4(self, jsonpath):
		with open(jsonpath, 'r') as f:
			data = json.load(f)
		keys = list(data.keys())
		values = list(data.values())
		return keys, values

	def manyquerykeys_in_para(self, keywords, para):
		count = 0
		for key in keywords:
				if key in para:
					count += 1
		return count == len(keywords) or count>=2
						 
	def get_re_query(self, query='说说机器人是什么'):
		
		def extract_nouns(sentence):
				words = pseg.cut(sentence)
				nouns = [word.word for word in words if word.flag.startswith('n')]
				return nouns

		query_keywords = list(set(extract_nouns(query)))
		match_keypara = []
		ans=[]
		for i in range(len(self.jsondata['关键词'])):
			keyword = self.jsondata['关键词'][i]
			para = self.jsondata['描述内容'][i]
			for query_keyword in query_keywords:
				if query_keyword in keyword or self.manyquerykeys_in_para(query_keywords, para):
					ans.append(i)
					match_keypara.append(keyword+":"+para)
		match_keypara = list(set(match_keypara))
		return ans
		if len(match_keypara) == 0:
			return ""
		else:
			res = ";\n\n".join(match_keypara)
			return res	# list
	# def get_bge_query(self, query='说说机器人是什么',anses=[]):
	# 	# Tokenize sentences
	# 	if query.startswith("介绍"):
	# 		encoded_input = self.tokenizer([query[2:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
	# 	elif query.startswith("说说"):
	# 		encoded_input = self.tokenizer([query[2:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
	# 	elif query.startswith("什么是"):
	# 		encoded_input = self.tokenizer([query[3:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
	# 	elif query.startswith("请介绍"):
	# 		encoded_input = self.tokenizer([query[3:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
	# 	else:
	# 		encoded_input = self.tokenizer([query], max_length=512, padding=True, truncation=True, return_tensors='pt')

	# 	sentence_embeddings = get_query_embedding(encoded_input)
	# 	# Compute token embeddings
	# 	# with torch.no_grad():
	# 	# 	model_output = self.model(**encoded_input)
	# 	# 	# Perform pooling. In this case, cls pooling.
	# 	# 	sentence_embeddings = model_output[0][:, 0]
		
	# 	# normalize embeddings
	# 	sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
		
	# 	# cal sim sentence
	# 	key_res = torch.mm(torch.Tensor(self.bgeKeywords['key']), sentence_embeddings.T)
	# 	# doc_res = torch.mm(torch.Tensor(self.numpydata['para']), sentence_embeddings.T)

	# 	# 旧的逻辑是，先匹配短的关键词，匹配上了就用，不然话就匹配doc的
	# 	# 新的逻辑：返回前两个关键词所匹配上的文本
	# 	# 测试新的逻辑：返回关键词和“描述内容”的top1
	# 	score_top1_key = float(key_res.max())
	# 	# score_top1_doc = float(doc_res.max())
	# 	#if score_top1_key < 0.6:
	# 	#	return ""
	# 	####print(anses)
	# 	####print(key_res.shape[0],key_res.shape[1])
	# 	for i in range(key_res.shape[0]):
	# 		if i not in anses:
	# 			key_res[i][0] = 0
	# 	####print(key_res)
	# 	####print(key_res.squeeze())
	# 	top3_values,_ = torch.topk(key_res.squeeze(), k=10, largest=True)
	# 	###print(top3_values)
	# 	if score_top1_key>0.8:
	# 		indices=torch.nonzero(key_res>=max(0.7,top3_values[9]), as_tuple=False).squeeze()
	# 	else:
	# 		indices=torch.nonzero(key_res>=max(0.1,top3_values[9]), as_tuple=False).squeeze()
	# 	###print(indices.dim())
	# 	if indices.dim()==1:
	# 		ind_top1_key = int(key_res.argmax())
	# 		keylist = self.jsondata['关键词']
	# 		doclist = self.jsondata['描述内容']
	# 		return '关键词：“'+keylist[ind_top1_key]+'”。描述内容：“'+doclist[ind_top1_key] +'”'
	# 	else:
	# 		indices = indices[:,0].tolist()
	# 		###print(indices)
	# 		ind_top1_key = int(key_res.argmax())
	# 		# ind_top1_doc = int(doc_res.argmax())
	# 		# key_res[key_res.argmax()] = 0
	# 		# ind_top2 = int(key_res.argmax())
	# 		keylist = self.jsondata['关键词']
	# 		doclist = self.jsondata['描述内容']
	# 		####print("bge score = ", score_top1_key)
	# 		ans=""
	# 		for i in indices:
	# 			ans += '关键词：“'+keylist[i]+'”。描述内容：“'+doclist[i] +'”\n'
	# 		#return '关键词：“'+keylist[ind_top1_key]+'”。描述内容：“'+doclist[ind_top1_key] +'”'
	# 		return ans
	# 	return ""

	def get_bge_query_2(self, query='说说机器人是什么'):
		# Tokenize sentences
		if query.startswith("介绍"):
			encoded_input = self.tokenizer([query[2:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
		elif query.startswith("说说"):
			encoded_input = self.tokenizer([query[2:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
		elif query.startswith("什么是"):
			encoded_input = self.tokenizer([query[3:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
		elif query.startswith("请介绍"):
			encoded_input = self.tokenizer([query[3:]], max_length=512, padding=True, truncation=True, return_tensors='pt')
		else:
			encoded_input = self.tokenizer([query], max_length=512, padding=True, truncation=True, return_tensors='pt')

		sentence_embeddings = get_query_embedding(encoded_input)
		print('************************')
		#print(sentence_embeddings)
		# Compute token embeddings
		# with torch.no_grad():
		# 	model_output = self.model(**encoded_input)
		# 	# Perform pooling. In this case, cls pooling.
		# 	sentence_embeddings = model_output[0][:, 0]
		
		# normalize embeddings
		sentence_embeddings = torch.nn.functional.normalize(torch.tensor(sentence_embeddings), p=2, dim=1)
		
		# cal sim sentence
		key_res = torch.mm(torch.Tensor(self.bgeKeywords_2['key']), sentence_embeddings.T)
		# doc_res = torch.mm(torch.Tensor(self.numpydata['para']), sentence_embeddings.T)

		# 旧的逻辑是，先匹配短的关键词，匹配上了就用，不然话就匹配doc的
		# 新的逻辑：返回前两个关键词所匹配上的文本
		# 测试新的逻辑：返回关键词和“描述内容”的top1
		score_top1_key = float(key_res.max())
		_ = float(key_res.min())
		print(score_top1_key,_)
		# score_top1_doc = float(doc_res.max())
		if score_top1_key < 0.65:
			return ""
		####print(anses)
		####print(key_res.shape[0],key_res.shape[1])

		####print(key_res)
		####print(key_res.squeeze())
		top3_values,_ = torch.topk(key_res.squeeze(), k=100, largest=True)
		###print(top3_values)
		#if score_top1_key>0.8:
		#	indices=torch.nonzero(key_res>=max(0.7,top3_values[9]), as_tuple=False).squeeze()
		#else:
		indices=[]
		for ii in range(100):
			indice=torch.where(key_res==top3_values[ii])
			indices.extend(indice[0].tolist())
		###print(indices)
		#indices=torch.nonzero(key_res>=max(0.1,top3_values[99]), as_tuple=False).squeeze()
		####print(indices)
		####print(indices.dim())
		# if indices.dim()==1:
		# 	ind_top1_key = int(key_res.argmax())
		# 	keylist = self.jsondata_2['关键词']
		# 	doclist = self.jsondata_2['描述内容']
		# 	return '关键词：“'+keylist[ind_top1_key]+'”。描述内容：“'+doclist[ind_top1_key] +'”'
		# else:
		# 	indices = indices[:,0].tolist()
		# 	###print(indices)
		# 	ind_top1_key = int(key_res.argmax())
		# 	# ind_top1_doc = int(doc_res.argmax())
		# 	# key_res[key_res.argmax()] = 0
		# 	# ind_top2 = int(key_res.argmax())
		keylist = self.jsondata_2['关键词']
		doclist = self.jsondata_2['描述内容']
		# 	####print("bge score = ", score_top1_key)
		keys=set()
		for i in indices:
			keys.add(keylist[i])
			if len(keys)==5:
				break
		keys=list(keys)

		ans=""
		for j in range(len(self.jsonalldata['关键词'])):
			if self.jsonalldata['关键词'][j] in keys:
				ans+='关键词：“'+self.jsonalldata['关键词'][j]+'”。描述内容：“'+self.jsonalldata['描述内容'][j] +'”\n'
		#for i in indices:
		#	ans += '关键词：“'+keylist[i]+'”。描述内容：“'+doclist[i] +'”\n'
		#return '关键词：“'+keylist[ind_top1_key]+'”。描述内容：“'+doclist[ind_top1_key] +'”'
		return ans
		#return ""

	def get_sim_score_from_3090(self, query):
		d = {
			"query":query
		}
		ws.send(json.dumps(d))
		response = ws.recv()
		mm_res = json.loads(response)
		mm_res = mm_res['mm_res']
		return mm_res
	def get_sim_score_from_3090_scr(self,query):
		d = {
			"query":query
		}
		ws.send(json.dumps(d))
		response = ws.recv()
		mm_res = json.loads(response)
		#print(mm_res)
		mm_res = mm_res['ans']
		return mm_res
	def get_bge_query_wmj(self, query='说说机器人是什么'):
		time1 = datetime.now()
		mm_res = self.get_sim_score_from_3090(query)
		time2 = datetime.now()
		timecost = time2-time1
		print(timecost)
		keylist = self.jsondata_2['关键词']
		# doclist = self.jsondata_2['描述内容']

		# 收集top5分数的关键词key
		top_keys = list()
		# top_docs = list()

		# 参考文本的数量
		ref_number = 5
		# 相似度分数的阈值
		sim_threshold = 0.7
		
		for _ in range(ref_number):
			# 获取分数最大的下标
			max_indice = np.argmax(mm_res)
			# 获取最大的分数
			max_score = mm_res[max_indice]
			# 获取最大的分数对应的关键词
			max_key = keylist[max_indice]
			# max_doc = doclist[max_indice]
			# print(max_key)
			# print(max_doc)
			# 一旦分数太低，就不要了
			if max_score < sim_threshold:
				break
			# 如果分数是可以的，就加上
			top_keys.append(max_key)
			# top_docs.append(max_doc)
			# 将最大值置为0，循环取出第二大的
			mm_res[max_indice] = 0
		ans = ""
		for j in range(len(self.jsonalldata['关键词'])):
			if self.jsonalldata['关键词'][j] in top_keys:
				ans += '关键词：“' + self.jsonalldata['关键词'][j] + '”。描述内容：“' + self.jsonalldata['描述内容'][j] + '”\n'
		return ans
	def get_bge_query_scr(self,query='说说机器人是什么'):
		time1 = datetime.now()
		mm_res = self.get_sim_score_from_3090_scr(query)
		time2 = datetime.now()
		timecost = time2-time1
		print(timecost)
		return mm_res

class client_qa:
	def __init__(self):
		self.history = []
		self.cur_document = ""
	def cur_dialogue(self):
		return str(self.history[-2:])
	
	def qa_append(self,dict_):
		self.history.append(dict_)
		return
	
	def has_history(self):
		return len(self.history)>0
	def show(self):
		if not self.has_history():
			print("无对话历史\n")
		else:
			print(self.cur_dialogue())


if __name__ == "__main__":
	scr = Searchscr()
	# aaa = input("输入：")
	querys = [
		'给我介绍一下空间灵巧手。',
		'他是什么时候成功发射的呀？',
		# '介绍一下玉兔号月球车',
		# '他是什么时候发射到月球上的？',
		# '介绍一下空间灵巧手',
		# '它是什么时候发射的',
		# '应该换一个'
		# '对，可以',
		# '今天是几号',
		# '小机械臂是如何使用的',
		# '空间灵巧手技术获得过什么奖项',
		# '介绍一下大机械臂',
	]
	for q in querys:
		
		document = scr.get_bge_query_wmj(q)
		print(document)
		# time.sleep(10)

if __name__ == "__main____":
	query1 = '你好'
	query2 = '你不好'
	tokenizer = AutoTokenizer.from_pretrained('/home/robot/.cache/huggingface/hub/models--infgrad--stella-large-zh-v3-1792d/snapshots/d5d39eb8cd11c80a63df53314e59997074469f09')
	encoded_input1 = tokenizer([query1], max_length=512, padding=True, truncation=True, return_tensors='pt')
	encoded_input2 = tokenizer([query2], max_length=512, padding=True, truncation=True, return_tensors='pt')

	sentence_embeddings1 = get_query_embedding(encoded_input1)
	sentence_embeddings2 = get_query_embedding(encoded_input2)
	
	
	sentence_embeddings1 = torch.nn.functional.normalize(torch.tensor(sentence_embeddings1), p=2, dim=1)
	sentence_embeddings2 = torch.nn.functional.normalize(torch.tensor(sentence_embeddings2), p=2, dim=1)
	
	# sentence_embeddings1 = torch.Tensor([[1,0,0]])
	# sentence_embeddings2 = torch.Tensor([[-1,0,1]])
 	
	# cal sim sentence
	key_res = torch.mm(sentence_embeddings1, sentence_embeddings2.T)
	print('-----', key_res)
	
	from numpy import dot
	from numpy.linalg import norm

	a = sentence_embeddings1[0].cpu().numpy()
	b = sentence_embeddings2[0].cpu().numpy()
	cos_sim = dot(a, b)/(norm(a)*norm(b))
	print(cos_sim)