
# ------------------------------
# Author: hsong
# 工具函數
# ------------------------------
import time
import jieba
import json
import pandas as pd
from typing import List, Tuple, Dict
# import debugpy # 导入包，可以放在前面

# debugpy.connect(('192.168.1.50', 6789)) # 与跳板机链接，"192.168.1.50"是hpc跳板机内网IP，6789是跳板机接收调试信息的端口
# debugpy.wait_for_client() # 等待跳板机的相应
# debugpy.breakpoint() # 断点。一般而言直接在vscode界面上打断点即可。这个通过代码的方式提供一个断点，否则如果忘了在界面上打断点程序就会一直运行，除非点击停止按钮。

# sentences = [
#     "你好！",
#     "你叫什么名字？",
#     "中国第一颗人造卫星叫什么名字？",
#     "介绍一下两弹一星？",
#     "中国是第几个发射卫星的国家？",
#     "中国航天日是哪一天？",
#     "长征五号是什么时候发射的？",
#     "介绍一下北斗卫星？",
#     "北斗卫星能做什么？",
#     "你继续讲。",
#     "你继续说。",
#     "哈工大航天馆成立于什么时候?",
#     "二楼展厅展示的是什么？",
#     "介绍一下哈工大在航天领域的科研成果",
# ]

def txts2ppls(sentences:List[str], ft_model:str='bert', ft_data:str='t1', epoch:int=40) -> List[float]:
    """给定['你继续说', '你好'], 返回[1.4, 2.1]的ppl

    """
    record = []
    M = ft_model
    # print(f"\033[33mmodel: {ft_model} ft data: {ft_data}.txt epoch: {epoch}\033[0m")
    from models import MaskedBert, MaskedAlbert
    model = MaskedBert.from_pretrained(
    path=f"./chinese_bert_wwm_ext_pytorch_{ft_data}_epoch{epoch}",
    device="cpu",  # 使用cpu或者cuda:0，default=cpu
    sentence_length=50,  # 长句做切句处理，段落会被切成最大不超过该变量的句子集，default=50
)
    for s in sentences:
        ppl = model.perplexity(
            x=" ".join(s),   # 每个字空格隔开或者输入一个list
            verbose=False,     # 是否显示详细的probability，default=False
            temperature=1.0,   # softmax的温度调节，default=1
            batch_size=100,    # 推理时的batch size，可根据cpu或gpu而定，default=100
        )
        # print(f"ppl: {ppl:.5f} # {s}")
        record.append(ppl)
    model.perplexity(sentences, verbose=True)
    return record

from typing import Union, List, Dict 

def get_ppl_for(sentence:Union[List[str],str]):  # 1句
    if not isinstance(sentence, List):
        sentence = [sentence]
    from models import MaskedBert, MaskedAlbert
    model = MaskedBert.from_pretrained(
    path="/home/kuavo/catkin_dt/src/voice_pkg/scripts/interrupt/PPL/chinese_bert_wwm_ext_pytorch_t2_epoch40",
    device="cpu",  # 使用cpu或者cuda:0，default=cpu
    sentence_length=50,  # 长句做切句处理，段落会被切成最大不超过该变量的句子集，default=50
    )
    ppls = []
    for s in sentence:
        ppl = model.perplexity(
            x=" ".join(s),   # 每个字空格隔开或者输入一个list
            verbose=False,     # 是否显示详细的probability，default=False
            temperature=1.0,   # softmax的温度调节，default=1
            batch_size=100,    # 推理时的batch size，可根据cpu或gpu而定，default=100
        )
        print(f"ppl: {ppl:.5f} # {s}")
        ppls.append(ppl)
    #model.perplexity(sentences[-4], verbose=True)   
    return ppls
    

def calcu_ppl_to_json(data_path:str='../DATAs/data.json',save_path:str='data_with_ppl.json') -> None:
    
    with open(data_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for item in data:
        id = item['id']
        question = item['question']
        if 'ppls' not in item:
            item['ppls'] = {}
            
        keys = list(item['answers'].keys())
        
        for key in keys:
            sentences = item['answers'][key]
            ppls = txts2ppls(sentences=sentences, ft_data='t2', ft_model='bert', epoch=40)
            add_key = key + '_ppls'
            if add_key not in item['ppls']:
                item['ppls'][add_key] = []
                
            item['ppls'][add_key] = ppls

    with open(save_path, 'w', encoding='utf-8') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    calcu_ppl_to_json()
