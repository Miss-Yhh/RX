from .LLM.apply1 import task_class
from .LLM.SQ_QA_1 import DocumentQA

def get_task_type(text=None, model='gpt-4', mode='llm'):
    """
    输入一段文本，返回任务类型（导航，继续，睡眠，问答）
    param text: 待判断的文本
    param keyword_list: 导航目标点（各种展厅）列表
    param exhibition: 当前位置的名称
    param extra_information: 关于当前位置的额外信息
    param model: 大模型类型，候选 'gpt-4' 'chatglm' 'gpt-3.5-turbo'
    param mode: 识别任务类型的方案，正则或大模型，候选 're' 'llm'
    """
    return task_class(text=text, model=model)

def get_llm_answer(model='huozi', stream_bool=True):
    """
    输入模型类型，返回一个支持多轮问答的模型类，通过 doc_qa_class.process_query("问题示例") 来调用
    param text: 待判断的文本
    param model: 大模型类型，候选 'gpt-4' 'huozi'
    """
    if model == 'huozi'or model == 'gpt-4' or model == 'chatglm' or model == 'qwen1_5':
        doc_qa_class = DocumentQA(model=model, stream_bool=stream_bool, debug_bool=True)
    else:
        assert("Model Not Support.")

    # doc_qa_class.process_query("介绍一下北斗卫星")
    return doc_qa_class