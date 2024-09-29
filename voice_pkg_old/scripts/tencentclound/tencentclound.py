from datetime import datetime
import json
import wave
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models
# pip install tencentcloud-sdk-python

import speech_recognition as sr 
import base64
import _thread as thread

from pydub.playback import play
from pydub import AudioSegment
import audioop
import json
def get_text(wav_path):
    with open(wav_path, "rb") as fp:
        data = fp.read()
    with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
        config = json.load(fj)
    SecretId, SecretKey = config['tencentcloud_SecretId'], config['tencentcloud_SecretKey']
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(SecretId, SecretKey)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "asr.ap-beijing.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = asr_client.AsrClient(cred, "", clientProfile)
        # client = asr_client.AsrClient(cred, "")

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.SentenceRecognitionRequest()
        params = {
            "EngSerViceType": "16k_zh",
            "SourceType": 1,
            "VoiceFormat": "wav",
            "Data":base64.b64encode(data).decode(encoding='utf-8'),
            "DataLen": len(data),
            "WordInfo": 2
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个SentenceRecognitionResponse的实例，与请求对象对应
        resp = client.SentenceRecognition(req)
        # 输出json格式的字符串回包
        return resp.Result

    except TencentCloudSDKException as err:
        print(err)
flagover = False

def run_iamhere():
    iamhere = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere.mp3'
    play(AudioSegment.from_mp3(iamhere)+10)
    global flagover
    flagover = True

def run_ding():
    finename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/ding_cut.mp3'
    play(AudioSegment.from_mp3(finename)+10)
    global flagover
    flagover = True

def get_wav(audio_file, input='ding'):
    # 打开麦克风录音
    r = sr.Recognizer()
    global flagover
    r.energy_threshold = 400   # threshold for background noise 
    r.pause_threshold = 0.8   # minimum length of silence (in seconds) that will register as the end of a phrase.  
    # try:
    if input == 'zai':
        # thread.start_new_thread(run_iamhere, ())
        run_iamhere()
    # with sr.Microphone() as source1:
    #     # calibrate ambient noise
    #     r.adjust_for_ambient_noise(source1, duration=0.8)
    # print(r.energy_threshold)
    thread.start_new_thread(run_ding, ())
    while flagover == False: continue

    with sr.Microphone() as source:     
        # r.listen start recording when there is audio input higher than threshold (set this to a reasonable number),
        # and stops recording when silence >0.8s(changable)
        time1 = datetime.now()
        print("I start listen....", time1)
        # audio = r.listen(source, timeout=6, phrase_time_limit=8)
        audio = r.listen(source, phrase_time_limit=8)
        print("I finish listen....", datetime.now()-time1)

        # get wav data from AudioData object 
        wav = audio.get_wav_data(convert_rate=16000, convert_width=2) # width=2 gives 16bit audio.

        # 保存 wav
        wf = wave.open(audio_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(wav)
        wf.close()
        print('sr is over', datetime.now())

    # 应用声音增益算法，增加分贝
    # sound = AudioSegment.from_file(audio_file, "wav") #加载WAV文件
    # sound = sound.apply_gain(10)
    # sound.export(audio_file, format="wav")
    # except sr.exceptions.WaitTimeoutError as e:
    #     print(e)
    #     return  

def iat_tencent(text='ding'):
    audio_file = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/mic_new_new_new_takeoff_0.wav'
    # get_wav(audio_file, input='ding')
    print('finish mic: ', datetime.now())
    # audio_file = '/home/robot/catkin_zt/src/voice_pkg/temp_record/111.wav'
    res = get_text(audio_file)
    print('result: ', res, datetime.now())
    return res

if __name__ == "__main__":
    # 测试时候在此处正确填写相关信息即可运行
    iat_tencent(text='ding')
    # time1 = datetime.now()

    # audio_file = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/mic.wav'
    # get_wav(audio_file)
    # print('finish mic: ', datetime.now()-time1)
    # # audio_file = '/home/robot/catkin_zt/src/voice_pkg/temp_record/111.wav'
    # res = get_text(audio_file)
    # print('result: ', res, datetime.now()-time1)