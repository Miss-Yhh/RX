import base64
import json
import os
import sys
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tts.v20190823 import tts_client, models
from playsound import playsound
def get_tts(text, savepath):
    try:
        with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
            config = json.load(fj)
        SecretId, SecretKey = config['tencentcloud_SecretId'], config['tencentcloud_SecretKey']
    
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(SecretId, SecretKey)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tts.ap-beijing.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = tts_client.TtsClient(cred, "ap-beijing", clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.TextToVoiceRequest()
        params = {
            "Text": text,
            "SessionId": "session-1234",
            "Volume": 1,
            "Speed": 1,
            "VoiceType": 101002
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个TextToVoiceResponse的实例，与请求对象对应
        resp = client.TextToVoice(req)
        # 输出json格式的字符串回包
        # resjson = resp.to_json_string()
        audio = resp.Audio
        audio = base64.b64decode(audio)
        print(type(audio))
        # audio = resp.Response.Audio
        if os.path.exists(savepath):
            os.remove(savepath)
        with open(savepath, 'ab') as f:
            f.write(audio)

    except TencentCloudSDKException as err:
        print(err)
    newpath = savepath.replace(".wav", "new.wav")
    cmd = f"ffmpeg -i {savepath} -acodec pcm_s16le -ac 1 -ar 16000 -y {newpath}"
    exit_status = os.system(cmd)
    print('-------tts is over----------')

# if __name__ == "__main__":
#     templis = {
#         'iamhere': '我在：', 
#         'error_no_question':'没有听到您的提问', 
#         'sorryforunderstanding':'很抱歉，我没有理解你的指令', 

#         'error_tts':'很抱歉，语音合成出错。',
#         'error_iat':'很抱歉，语音听写出错。', 

#         'leadtoallexhibit':'好的，我将带大家参观全部展区。', 
#         'goonexhibit':'那我们就继续吧', 
#         'exitexhibit':'那我们的讲解就先到这里吧', 

#         'okwmj':'好的',
#         'byewmj':'好，我先退出了。', 
#         'byewmj1':'那我先退出了。', 

#         'answerover':'我回答完了', 
#         'anyquestions':'大家还有什么问题吗？ ',
#         'oknomorequestions':'好，没有问题我就先退出了',

#         'askagain':'您可以重新唤醒我提问',

#         "thinking0":'听到您的问题啦，请让我思索片刻',
#         "thinking1":'好的，请让我思索一下',
#         "thinking2":'这个问题我需要思考一下',
#     }
#     SavePath = '/home/robot/catkin_zt/src/zt_ros/scripts/kedaxunfei/testmic.wav'
#     # for k, v in templis.items():
#     #     print(k, v)
#     #     SavePath = os.path.join('/home/lemon/catkin_zt/src/zt_ros/scripts/tencentclound/temp_record', f'{k}.wav')
#     #     playsound_tts(v, SavePath)
#     #     playsound(SavePath)

if __name__ == "__main__":
    # with open("/home/kuavo/catkin_dt/src/voice_pkg/temp_record/tts_sentence.txt", "r") as f:
    #   textinput = f.read()
    # textinput = '你好啊，我叫七哥'
    savepath = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/play.wav'
    text = sys.argv[1]
    get_tts(text, savepath)