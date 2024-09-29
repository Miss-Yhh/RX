import re

from ..LLM import sleep_judge

def analyze_text(text, keyword_list, extra_information, model, mode):
    if mode == 're':    
        # 第一步：使用正则表达式匹配
        for keyword in keyword_list:
            if re.search(keyword, text):
                return '参观'+' '+str(keyword)
            
        # 第二步：使用正则表达式匹配
        if re.search('继续', text):
            return '继续'
        
        # 第三步：调用自定义函数
        if sleep_judge(text=text, model=model, mode=mode) == '是':
            return '休眠'
        
        # 如果前两步都没有触发返回，则返回'C'
        return '问答'
    
    elif mode == 'llm':
        return sleep_judge(text=text, extra_information=extra_information, model=model, mode=mode)

if __name__ == '__main__':
    pass
