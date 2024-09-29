# ===================================
# Author: hsong
# 小模型，给定文本，输出匹配的预定义动作
# ===================================
from sentence_transformers import SentenceTransformer
import time
import numpy as np
import json

# _model = SentenceTransformer('BAAI/bge-large-zh-v1.5')  # 1.3G
# _model = SentenceTransformer('BAAI/bge-base-zh-v1.5')   # 409M
# _model = SentenceTransformer('BAAI/bge-small-zh-v1.5')  # 100M-200M
# 效果递减

#_model = SentenceTransformer('BAAI/bge-small-zh-v1.5', cache_folder="/home/kuavo/catkin_dt/src/checkpoints/bge_small_zh_v1.5")
_model = SentenceTransformer('BAAI/bge-large-zh-v1.5', cache_folder="/home/kuavo/catkin_dt/src/checkpoints/bge_large_zh_v1.5")

def get_action_from(txt:str, _model:object=_model):
    """给定一段文本，匹配合适的动作
    Args:
        txt (str): 输入文本
        _model (object, optional): 模型. Defaults to _model.
    Returns:
        str: 匹配到的动作
        None: 无匹配
    """
    #actions = ["招手", "举左手", "举右手","向前指","向上指","向后转", "摊手", "指向我自己"]

    filename = '/home/kuavo/catkin_dt/src/actions.json'

    with open(filename, 'r', encoding='utf-8') as f:
        actions_list = json.load(f)
        
    #print(actions_list)
    
    actions = [_["action_name"] for _ in actions_list]
    ids = [_["id"] for _ in actions_list]
    #print(actions)
    embeddings_1 = _model.encode(txt, normalize_embeddings=True)
    # print(embeddings_1)
    embeddings_2 = _model.encode(actions, normalize_embeddings=True)
    # print(embeddings_2)
    similarity = embeddings_1 @ embeddings_2.T
    print(f"输入句子：{txt}:")
    print(similarity)
    print(actions)
    argmax = np.argmax(similarity)
    id = ids[argmax]
    #print(argmax)
    if similarity[argmax] > 0.4:
        print(f"输出动作：\033[33m{actions[argmax]} id:{id}\033[0m")
        print(" ")
        return actions[argmax], id
    else:
        print('\033[33m没有适合的动作\033[0m')
        print(" ")
        return None

if __name__=="__main__":

    txt = [
        "你好", 
        "再见",
        "请看左边这个展品",
        "请看右边这个展品", 
        "请看前方离我们较近的这个展品", 
        "请看前方离我们较远的的这个展品"
        "请看上面这个展品",
        "我们",
        "请看后面这个展品",
        "给大家介绍一下",
        "介绍一下风云4号",
        "好了我介绍完了",
        "来合影留念吧"
        ]
    for i in txt:
        a = time.time()
        action, id = get_action_from(i)
        b=time.time()
        print(f"TIME: {b-a} s")
        
        #action = get_action_from("你好")
        """actions labels:
        ['招手',
        '介绍自己',
        '介绍正右方',
        '介绍右方',
        '介绍较近的前方',
        '介绍较远的前方',
        '回忆 刚刚我们',
        '复杂的讲解动作',
        '讲解结束 合影 介绍完毕 姿势']
        """
        
        
        
    """调用示例
    from get_action_from_text import get_action_from
    action，id = get_action_from(txt = "你好")
    """
