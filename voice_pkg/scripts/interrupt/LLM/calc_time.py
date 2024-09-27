f = open('ernie_answers.txt','r',encoding='utf-8')
sentences=[]
for line in f.readlines():
    sentences.append(line.strip())
cnt=0
tim=0
for sentence in sentences:
    if sentence.startswith('回复时间') and '哦豁' not in sentence:
        cnt+=1
        tim+=float(sentence.split('：')[1])

print(tim/max(cnt,1))
