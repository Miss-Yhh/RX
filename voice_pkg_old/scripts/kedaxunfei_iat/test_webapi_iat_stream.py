#!/home/lemon/anaconda3/envs/zt/bin/python
# -*- coding:utf-8 -*-
#
#	 author: iflytek
#
#	本demo测试时运行的环境为：Windows + Python3.7
#	本demo测试成功运行时所安装的第三方库及其版本如下，您可自行逐一或者复制到一个新的txt文件利用pip一次性安装：
#	 cffi==1.12.3
#	 gevent==1.4.0
#	 greenlet==0.4.15
#	 pycparser==2.19
#	 six==1.12.0
#	 websocket==0.2.1
#	 websocket-client==0.56.0
#
#	语音听写流式 WebAPI 接口调用示例 接口文档（必看）：https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
#	webapi 听写服务参考帖子（必看）：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947&extra=
#	语音听写流式WebAPI 服务，热词使用方式：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--个性化热词，
#	设置热词
#	注意：热词只能在识别的时候会增加热词的识别权重，需要注意的是增加相应词条的识别率，但并不是绝对的，具体效果以您测试为准。
#	语音听写流式WebAPI 服务，方言试用方法：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--识别语种列表
#	可添加语种或方言，添加后会显示该方言的参数值
#	错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import os
import queue
import wave
import websocket
import datetime
import shutil
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
# import _thread as thread
import threading
# import speech_recognition as sr 
# pip install SpeechRecognition

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models

from pydub.playback import play
from pydub import AudioSegment

import rospy


STATUS_FIRST_FRAME = 0	# 第一帧的标识
STATUS_CONTINUE_FRAME = 1	# 中间帧标识
STATUS_LAST_FRAME = 2	# 最后一帧的标识

flagover = False	# 提示音是否已经读完
micover = False	# False: 还没录音完 True 录音结束
iatover = False	# False: 每次识别结束都会改为True
ifinter = False	# 判断是否打断
has_sound = False	# 判断是否有人说话
text = ''
card_ = 0	# 声卡

now = None

DURATION = 10 # 每 $DURATION 秒录音一次
THRESHOLD_AUDIO = 3 # 音量的能量超过阈值 $THRESHOLD_AUDIO，说明有人说话，继续录音


class Ws_Param(object):
		# 初始化
		def __init__(self, APPID, APIKey, APISecret):
				self.APPID = APPID
				self.APIKey = APIKey
				self.APISecret = APISecret
				self.result = ''

				# 公共参数(common)
				self.CommonArgs = {"app_id": self.APPID}
				# 业务参数(business)，更多个性化参数可在官网查看
				self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":0,"vad_eos":10000,"dwa":"wpgs"}

		# 生成url
		def create_url(self):
				url = 'wss://ws-api.xfyun.cn/v2/iat'
				# 生成RFC1123格式的时间戳
				now = datetime.now()
				date = format_date_time(mktime(now.timetuple()))

				# 拼接字符串
				signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
				signature_origin += "date: " + date + "\n"
				signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
				# 进行hmac-sha256进行加密
				signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
																 digestmod=hashlib.sha256).digest()
				signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

				authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
						self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
				authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
				# 将请求的鉴权参数组合为字典
				v = {
						"authorization": authorization,
						"date": date,
						"host": "ws-api.xfyun.cn"
				}
				# 拼接鉴权参数，生成url
				url = url + '?' + urlencode(v)
				return url

def kedaxunfei_iat_service(wsParam):
		time1 = datetime.now()
		def on_message(ws, message):
				# try:
				message = json.loads(message)
				# print(message)
				code = message["code"]
				sid = message["sid"]
				if code != 0:
						errMsg = message["message"]
						print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
				else:
						result = message["data"]["result"]
						ws_data = result["ws"]
						iflast = result["ls"]
						pgs = result["pgs"]
						result = ""
						for i in ws_data:
								for w in i["cw"]:
										result += w["w"]
						if pgs == 'rpl':
								wsParam.result = result
						else:
								wsParam.result += result
						# print(wsParam.result)
						if iflast:
								# print('正常关闭前：', datetime.now())
								ws.close()
								# print('正常关闭后：', datetime.now())
				
				# except Exception as e:
				# 		print("receive msg,but parse exception:", e, datetime.now())
				# 		ws.close()
				# 		return


		# 收到websocket错误的处理
		def on_error(ws, error):
				print("### error:", error, datetime.now())
				ws.close()


		# 收到websocket关闭的处理
		def on_close(ws,a,b):
				pass
				# print("### closed ###", datetime.now())
				# print(a)
				# print(b)

		def get_buf(status, wsParam, buf):
			# 第一帧处理
			# 发送第一帧音频，带business 参数
			# appid 必须带上，只需第一帧发送
			if status == STATUS_FIRST_FRAME:
					d = {"common": wsParam.CommonArgs,
									"business": wsParam.BusinessArgs,
									"data": {"status": 0, "format": "audio/L16;rate=16000",
													"audio": str(base64.b64encode(buf), 'utf-8'),
													"encoding": "raw"}}
					# print('send first audio')
			# 中间帧处理
			elif status == STATUS_CONTINUE_FRAME:
					d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
													"audio": str(base64.b64encode(buf), 'utf-8'),
													"encoding": "raw"}}
					# print('send mid audio')
			# 最后一帧处理
			elif status == STATUS_LAST_FRAME:
					d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
													"audio": str(base64.b64encode(buf), 'utf-8'),
													"encoding": "raw"}}
					# print('send last audio')
			# 模拟音频采样间隔
			return d
 
		# 收到websocket连接建立的处理
		def on_open(ws):
				def run(ws):
					global ifinter
					ifinter = False

					global has_sound
					has_sound = False	# 是否有人在说话
					start_speak = False	 # 是否有人开始说话

					# 定义音频录制的参数
					FORMAT = pyaudio.paInt16	# 数据格式
					CHANNELS = 1	# 通道数，这里假设你有6个麦克风
					RATE = 16000	# 采样率
					CHUNK = 1000	# 每次读取的数据块大小
					RECORD_SECONDS = 10	# 录制时间
					
					status = STATUS_FIRST_FRAME	# 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧
					
					# 初始化PyAudio
					p = pyaudio.PyAudio()

					# 打开音频流
					stream = p.open(format=FORMAT,
													channels=CHANNELS,
													rate=RATE,
													input=True,
													frames_per_buffer=CHUNK,
													# input_device_index=1
													)

					print("Recording:", end='')

					threshold = 3	# 音量的能量
					# 开始录制
					total_valid_frames = 0
					somebodytalking_duration = RATE / CHUNK * 0.2
					stopduration = int(RATE / CHUNK * 1)
					bufferlength = int(RATE / CHUNK * 0.5)
					total_frames = int(RATE / CHUNK * RECORD_SECONDS)
					# print(total_frames)
					step = 0
					
					# 准备音频frame的buffer
					buffers = queue.deque()
					# audio_q = queue.deque()
					str2terminal = queue.deque()
					for i in range(19):
						str2terminal.append('-')
					while step < total_frames:
						if ifinter:
							# 获取当前线程的对象
							# current_thread = threading.current_thread()
							# 打印当前线程的名称和标识符
							# print(f"录音被打断！！！Thread Name: {current_thread.name}, Thread ID: {current_thread.ident}")
							# 
							# 停止和关闭流
							# print('流式关闭后：', datetime.now())
							# 注意：要先关闭麦克风流式，保证下一次打开麦克风是成功的
       				# 因为若先关闭了ws，可能会导致麦克风无法正常关闭！！
							stream.stop_stream()
							stream.close()
							p.terminate()
							# print('流式关闭后：', datetime.now())
							
							# print('打断关闭前：', datetime.now())
							ws.close()
							# print('打断关闭后：', datetime.now())
							return
						step += 1
						buf = stream.read(CHUNK)
						frame = np.frombuffer(buf, dtype=np.int16)
						energy = np.linalg.norm(frame) // 10000
						# print(energy)
						
						# 如果有声音了，那就加入为frame
						if energy > threshold:
								start_speak = True
						if start_speak:
								buffers.append(buf)
						if len(buffers) > bufferlength:
								buffers.popleft()
						
						# 一听到有声音,现在的step就重置为0，并且静默的时间又回归0.8秒
						if energy > threshold:
								total_valid_frames += 1
								if has_sound == False and total_valid_frames > somebodytalking_duration:
										# 如果超过了一秒都有声音，说明有人说话了
										has_sound = True
								str2terminal.append(f'{int(energy)} ')
								str2terminal.popleft()

								# 持续录制，不会停止
								step = 0
								# 防止说话到一半有继续说，此时应当保证静默时间 仍然是从0.8秒开始减
								aftersound_frames = stopduration
						else:
								str2terminal.append('-')
								# print('-=-=-=-',datetime.now())
								str2terminal.popleft()
						print("\r"+"".join(str2terminal), end='')
						
						# 一旦不再听到声音了，就计算是否到了静默时间
						if energy <= threshold and has_sound == True:
								aftersound_frames -= 1
								if aftersound_frames < 0:
										# 如果说话之后的静默时间超过一秒
										break
						
						# 发送音频
						if len(buffers) == 1 and status == STATUS_FIRST_FRAME:
								# print('发送第一帧！！！')
								buf = buffers.popleft()
								# print('第一帧=', len(buf))
								d = get_buf(status, wsParam, buf)
								status = STATUS_CONTINUE_FRAME
								ws.send(json.dumps(d))
						# 中间帧处理
						elif status == STATUS_CONTINUE_FRAME:
								# print('发送中间帧！！！')
								if len(buffers) == 0:
									break
								buf = buffers.popleft()
								d = get_buf(status, wsParam, buf)
								ws.send(json.dumps(d))
					while len(buffers) != 0:
							# print('发送中间帧！！！???')
							buf = buffers.popleft()
							d = get_buf(status, wsParam, buf)
							ws.send(json.dumps(d))
							# 模拟录音的间隔
							time.sleep(0.04)
					# print('发送结束帧！！！???')
					d = get_buf(STATUS_LAST_FRAME, wsParam, b'')	# 最后一帧
					ws.send(json.dumps(d))

					print("\n录音结束。", datetime.now())

					# 写个文件记录时间
					with open('/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_iat/file.txt', 'w') as f:
						f.write(str(datetime.now()))
					if has_sound == True:
						# 最后等待一秒再关闭连接，保证最后的数据传过去了
						time.sleep(1)
						# print("录音结束。")
					# 关闭连接
					ws.close()
					
					# 停止和关闭流
					stream.stop_stream()
					stream.close()
					p.terminate()
				t = threading.Thread(target=run, args=(ws,))
				t.start()
				# thread.start_new_thread(run, (ws,))
		
		websocket.enableTrace(False)
		wsUrl = wsParam.create_url()
		ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
		ws.on_open = on_open
		ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
		# global ifinter
		# global text
		# if ifinter:
		# 	wsParam.result = text
		# 	print('打断或者触控板而返回')
		# # print(f"socket time cost final:{datetime.now()-time1}")
		# print("==", wsParam.result, "==", datetime.now())
		# print('-------iat is over----------')
		# return wsParam.result

def run_prompt_audio(filename):
		global card_
		if card_ == -1:
			play(AudioSegment.from_wav(filename))
		else:
			cmd = f"aplay -D plughw:{card_},0 {filename} > /dev/null 2>&1"
			exit_status = os.system(cmd)
		global flagover
		flagover = True

import wave
import pyaudio
import numpy as np
import subprocess

# class Mic_interupt():
#	 def __init__(self):
#		 # 测试时候在此处正确填写相关信息即可运行
#		 self.ivw_sub = rospy.Subscriber("ivw_chatter", String, ivw_callback) # 订阅ivw话题，唤醒词
#		 self.touch_sub = rospy.Subscriber("touchpad_chatter", String, touch_callback) # 订阅ivw话题，唤醒词
# mic_interupt = Mic_interupt() 

def ivw_callback(data):
	# rospy.loginfo(rospy.get_caller_id() + "I heard %s from ivw", data.data)
	print(f"收到小红小红的打断信号！现在可以打断", datetime.now())
	global ifinter
	ifinter = True
	global text
	text = '####'

def touch_callback(data):
	# rospy.loginfo(rospy.get_caller_id() + "I heard %s from ivw", data.data)
	print(f"收到触控板的打断信号！现在可以打断", datetime.now())
	global ifinter
	ifinter = True
	global text
	text = '$$$$'

from std_msgs.msg import String
ivw_sub = rospy.Subscriber("ivw_chatter", String, ivw_callback) # 订阅ivw话题，唤醒词
touch_sub = rospy.Subscriber("touchpad_chatter", String, touch_callback) # 订阅ivw话题，唤醒词


def iat_web_api(input, iter=1, environment_name='default', card=2):
	with open('/home/kuavo/catkin_dt/config_dt.json', 'r') as fj:
		config = json.load(fj)
	APPID, APISecret, APIKey = config['kedaxunfei_appid'], config['kedaxunfei_apiSecret'], config['kedaxunfei_appkey']
	wsParam = Ws_Param(APPID=APPID, 
					APISecret=APISecret,
					APIKey=APIKey
					)
	# 重置全局变量
	global card_
	card_ = card

	if input == 'zai':
			filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere_cut.wav'
	else:
			filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/ding_cut_small.wav'
	# thread.start_new_thread(run_prompt_audio, (filename,))
	# t = threading.Thread(target=run_prompt_audio, args=(filename,))
	# t.start()
	thread_kedaxunfei = threading.Thread(target=kedaxunfei_iat_service, args=(wsParam,))
	thread_kedaxunfei.start()
	global ifinter
	ifinter = False
	global text
	while thread_kedaxunfei.is_alive():
		# print("waiting kedaxunfei iat thread")
		if ifinter:
			wsParam.result = text
			print('语音打断或者触控板而返回')
			break
	# print("==", result, "==", datetime.now())
	print('识别结束。', datetime.now())
	print("==", wsParam.result, "==", datetime.now())
	print('-------iat is over----------')
	return wsParam.result

if __name__ == "__main__":
		# card_ = -1
		# res = iat_web_api(input='ding', iter=1, card=0)
		# print('res1 = ', res)
		cmd = "ffmpeg -loglevel quiet -i /home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/好的.wav -acodec pcm_s16le -ac 1 -ar 16000 -filter:a volume=+15dB -y /home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/好的louder.wav"
		os.system(cmd)
		# run_prompt_audio('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/ding_cut_small.wav')
		