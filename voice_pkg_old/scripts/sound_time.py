import yaml
import json
import wave
import contextlib
import os

# 从配置文件中加载指定展馆的讲解词
def get_config_explanation_words(config_path, hall_index):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)  # 使用yaml库加载配置文件
    all_speech = config['讲解词列表']  # 从配置中获取所有的讲解词
    commentaries = list(all_speech.keys())  # 获取所有键（展馆名）
    if hall_index >= len(commentaries):
        return None  # 如果索引超出范围，返回None
    return all_speech[commentaries[hall_index]]  # 返回指定索引的展馆讲解词

# 将文本分割成句子
def split_text_into_sentences(text):
    if not text:
        return []  # 如果文本为空，返回空列表
    splitters = [',', ';', '.','!','?',':', '，', '。', '！', "'", '；', '？', '：', '/'] # 遇到这些符号就拆分句子
    numbers = [str(c) for c in range(10)] # 遇到数字不拆分句子

    sentences = []
    sentence = "" # 用于存储句子
    pre_c = '' # 用于存储上一个字符

    # 遍历文本，切分段落为句子
    for c in (text):
        if c == '【':
            if sentence and sentence != ' ':
                sentences.append(sentence)
            sentence = c
            continue
        
        sentence += c
        # 一旦碰到标点符号，就判断目前的长度
        if c in splitters and len(sentence) > 8 + 6:
            if pre_c in numbers:
                continue
            sentences.append(sentence) # 加入句子列表
            sentence = ""
    if sentence:
        sentences.append(sentence)
    return sentences

# 获取音频文件的时长
def get_audio_duration(audio_path):
    with contextlib.closing(wave.open(audio_path, 'r')) as f:
        frames = f.getnframes()  # 获取音频帧数
        rate = f.getframerate()  # 获取音频的帧率
        duration = frames / float(rate)  # 计算音频时长
        return duration

# 主函数，遍历所有展馆并处理对应音频
def main():
    ACTOIN_TIME_DICT={
        '挥手动作':0,
        '礼仪讲解动作':2,
        '左手伸手指引':5.6,
        '右手伸手指引':3,
        '右手举起比1':4.5,
        '右手举起比2':4.5,
        '右手举起比3':4.5,
        '右手举起比5':4.5,
        '右手举起握拳':4.5,
        '左手平摊讲解动作':5.6,
        '右手平摊讲解动作':4.5,
        '左手前伸指引':4,
        '右手前伸指引':3,
        '先左后右平摊讲解动作':6,
        '双臂平举打开':4.5,
        '恢复行走状态':2,
        '礼仪讲解小幅度动作':8,
        '左手举起比1':5.6,
        '右手握拳在上左手张开做掌':6.6,
        '右手从1数到3':7,
        '右手举起比125':6
    }

    config_path = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/config/commentary_config0421.yaml'
    json_path = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech/qige.json'
    output_path = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech/qige_time.json'

    # 读取JSON文件中的音频映射
    with open(json_path, 'r+') as file:
        audio_mapping = json.load(file)

    # 准备存储句子及其音频时长的字典
    all_sentence_duration_mapping = {}
    hall_index = 0

    while True:
        text = get_config_explanation_words(config_path, hall_index)
        if text is None:
            break  # 如果无法获取文本，终止循环

        sentences = split_text_into_sentences(text)
        if not sentences:
            break  # 如果无法分割成句子，终止循环

        sentence_duration_mapping = {}
        found_audio = False

        for sentence in sentences:

            import re

            def find_and_replace_brackets(text):
                # 使用正则表达式查找并替换【】及其内容
                pattern = r"【(.*?)】"
                match = re.search(pattern, text)
                if match:
                    content = match.group(1)  # 提取括号内的内容
                    # 替换【xxx】为""
                    new_text = re.sub(pattern, '', text)
                    return "【"+content+"】", new_text
                else:
                    return '', text
            action_key, sentence = find_and_replace_brackets(sentence)

            audio_path = audio_mapping.get(sentence)
            if audio_path and os.path.exists(audio_path):
                duration = get_audio_duration(audio_path)  # 计算时长
                sentence_duration_mapping[action_key + sentence + ' ' + 
                                          str(ACTOIN_TIME_DICT.get(action_key[1:-1], 0)) + ' '] = duration
                found_audio = True  # 标记找到音频文件

        if not found_audio:
            print(f"No audio files found for hall index {hall_index}. Stopping.")
            break  # 如果没有找到任何音频文件，终止循环

        all_sentence_duration_mapping.update(sentence_duration_mapping)  # 更新总映射
        hall_index += 1  # 增加展馆索引

    # 将结果写入新的JSON文件
    with open(output_path, 'w') as file:
        json.dump(all_sentence_duration_mapping, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
