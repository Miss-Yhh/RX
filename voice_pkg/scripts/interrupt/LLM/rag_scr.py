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

import torch
import jieba.posseg as pseg

from transformers import AutoTokenizer, AutoModel

"""
忽略以下警告：
huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
To disable this warning, you can either:
				- Avoid using `tokenizers` before the fork if possible
				- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from transformers import AutoModelForCausalLM, AutoTokenizer
csv1 = '/Users/winstonwei/Documents/wmj_workspace/xiaohong/ZhanTing/voice_pkg/scripts/qa_legacy/qa_data/documents_lecture_all-v4.csv'
csv2 = '/Users/winstonwei/Documents/wmj_workspace/xiaohong/ZhanTing/voice_pkg/scripts/qa_legacy/qa_data/example.csv'
modelpath = '/Users/winstonwei/Documents/wmj_workspace/xiaohong/bge-small-zh-v1.5'
sentenembedding = '/Users/winstonwei/Documents/wmj_workspace/xiaohong/ZhanTing/voice_pkg/scripts/qa_legacy/qa_data/sentence_embeddings.pt'
class Searchscr:
	def __init__(self) -> None:
		#文档的基础csv
		csv_file_path = csv1
		df = pd.read_csv(csv_file_path)
		column0 = df['aaa分类'].tolist()
		column1 = df['关键词'].tolist()
		column2 = df['描述内容'].tolist()
		#逐句拆分文档后的csv
		df2=pd.read_csv(csv2)
		column0_2 = df2['关键词'].tolist()
		column1_2 = df2['描述内容'].tolist()
		self.jsondata={'关键词':column0_2, '描述内容':column1_2}
		self.jsonalldata={'分类': column0, '关键词':column1, '描述内容':column2}
		self.tokenizer = AutoTokenizer.from_pretrained(modelpath)
		self.model = AutoModel.from_pretrained(modelpath)
		self.model.eval()
		# self.update_embeddings_pt()
		self.bgeKeywords_jsondata = self.get_bge_embedding_pt()

	def update_embeddings_pt(self):
		# Tokenize sentences
		encoded_input = self.tokenizer(self.jsondata['描述内容'], max_length=512, padding=True, truncation=True, return_tensors='pt')
		# Compute token embeddings
		with torch.no_grad():
				model_output = self.model(**encoded_input)
				# Perform pooling. In this case, cls pooling.
				sentence_embeddings = model_output[0][:, 0]
		# normalize embeddings
		torch.save(sentence_embeddings, sentenembedding)

	def get_bge_embedding_pt(self):#获取描述内容的embedding
		sentence_embeddings=torch.load(sentenembedding)
		key_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

		# 保存embedding到numpy
		return {'key':key_embeddings, 'para':sentence_embeddings}

	def get_bge_query(self, query='说说机器人是什么'):
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

		# Compute token embeddings
		with torch.no_grad():
			model_output = self.model(**encoded_input)
			# Perform pooling. In this case, cls pooling.
			sentence_embeddings = model_output[0][:, 0]

		# normalize embeddings
		sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
		
		# cal sim sentence
		key_res = torch.mm(torch.Tensor(self.bgeKeywords_jsondata['key']), sentence_embeddings.T)
		# doc_res = torch.mm(torch.Tensor(self.numpydata['para']), sentence_embeddings.T)

		score_top1_key = float(key_res.max())
		top3_values,_ = torch.topk(key_res.squeeze(), k=100, largest=True)
		indices=[]
		for ii in range(100):
			indice=torch.where(key_res==top3_values[ii])
			indices.extend(indice[0].tolist())
		keylist = self.jsondata['关键词']
		doclist = self.jsondata['描述内容']
		# 选前七个可能的语段
		keys=set()
		for i in indices:
			keys.add(keylist[i])
			if len(keys)==7:
				break
		keys=list(keys)
		# 拼接文档
		ans=""
		for j in range(len(self.jsonalldata['关键词'])):
			if self.jsonalldata['关键词'][j] in keys:
				ans+='关键词：“'+self.jsonalldata['关键词'][j]+'”。描述内容：“'+self.jsonalldata['描述内容'][j] +'”\n'

		return ans


if __name__ == '__main__':
	query = '刘宏'
	rag_scr = Searchscr()
	document = rag_scr.get_bge_query(query)
	print(document)
 