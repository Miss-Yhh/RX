from funasr import AutoModel
# paraformer-zh is a multi-functional asr model
# use vad, punc, spk or not as you need
from datetime import datetime
model = AutoModel(model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch", model_revision="v2.0.4",
                  vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch", vad_model_revision="v2.0.4",
                  punc_model="iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch", punc_model_revision="v2.0.4",
                  # spk_model="cam++", spk_model_revision="v2.0.2",
                  )
time1 = datetime.now()
res = model.generate(input="/home/kuavo/catkin_dt/src/voice_pkg/temp_record/mic_z_016k.wav", 
            batch_size_s=5000, # 1 token = 60 ms
            hotword='魔搭')
time2 = datetime.now()
if len(res) > 0:
  res = res[0]['text']
else:
  res = ''
print(res)
print(time2-time1)
