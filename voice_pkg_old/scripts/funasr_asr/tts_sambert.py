import os
from modelscope.outputs import OutputKeys
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from datetime import datetime
import _thread as thread
from pydub.playback import play
from pydub import AudioSegment

text = 'hihi'
savepath1 = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo1.wav'
voice = 'zhiyan_emo'
model_id = 'iic/speech_sambert-hifigan_tts_zh-cn_16k'
# model_id = 'iic/speech_sambert-hifigan_tts_zhiyan_emo_zh-cn_16k'
# model_id = 'speech_tts/speech_sambert-hifigan_tts_zh-cn_multisp_pretrain_16k'
sambert_hifigan_tts = pipeline(task=Tasks.text_to_speech, model=model_id)

time1 = datetime.now()
output = sambert_hifigan_tts(input=text, voice=voice)
wav = output[OutputKeys.OUTPUT_WAV]
with open(savepath1, 'wb') as f:
    f.write(wav)
time2 = datetime.now()
print(time2-time1)

playing = False
def playsound_work(savepath):
  global playing
  playing = True
  cmd = f"aplay -D plughw:0,0 {savepath}"
  exit_status = os.system(cmd)
  playing = False
    
# thread.start_new_thread(playsound_work, (savepath1,))
text = '今天的天气真不错'

savepath2 = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo2.wav'
time1 = datetime.now()
output = sambert_hifigan_tts(input=text, voice=voice)
wav = output[OutputKeys.OUTPUT_WAV]
with open(savepath2, 'wb') as f:
    f.write(wav)
time2 = datetime.now()
print(time2-time1)
while playing == True:
  continue
thread.start_new_thread(playsound_work, (savepath2,))


text = '你的帽子真好看，你带上去了之后好帅啊！'

savepath3 = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo3.wav'
time1 = datetime.now()
output = sambert_hifigan_tts(input=text, voice=voice)
wav = output[OutputKeys.OUTPUT_WAV]
with open(savepath3, 'wb') as f:
    f.write(wav)
time2 = datetime.now()
print(time2-time1)
while playing == True:
  continue
thread.start_new_thread(playsound_work, (savepath3,))