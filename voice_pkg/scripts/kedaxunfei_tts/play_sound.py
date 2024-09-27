import pyaudio
from pydub.playback import play
from pydub import AudioSegment
import sys

# savepath = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/playnew.wav'

def playsound_work(savepath):
    play(AudioSegment.from_wav(savepath))
    
# from playsound import playsound
def play_sound():
    playsound(savepath)


import sounddevice as sd
import soundfile as sf

def sd_play():
    filename = '/home/kuavo/catkin_dt/src/voice_pkg/temp_record/iamhere.mp3'
    data, fs = sf.read(filename)  # 读取音频文件

    # 指定设备索引或名称播放音频
    device_name = 'Bothlent UAC Dongle: USB Audio'  # 你可以根据实际情况替换这里的设备名称

    sd.play(data, fs, device=1)

import pyaudio
import wave

def play_audio(savepath):
    # 打开WAV音频文件
    wf = wave.open(savepath, 'rb')

    # 创建PyAudio对象
    p = pyaudio.PyAudio()

    # 打开输出流
    print("channel:", wf.getnchannels())
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=1,
                    rate=wf.getframerate(),
                    output=True,
                    # output_device_index=2
                    )

    # 读取数据
    data = wf.readframes(4000)

    # 播放
    while data:
        stream.write(data)
        data = wf.readframes(4000)

    # 停止和关闭流
    stream.stop_stream()
    stream.close()

    # 关闭PyAudio
    p.terminate()



if __name__ == '__main__':
    savepath = sys.argv[1]
    # savepath = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/好的louder.wav'
    # playsound_work(savepath)
    # thread.start_new_thread(, (savepath, ))
    '''
ffmpeg -i /home/kuavo/catkin_dt/src/voice_pkg/temp_record/playtest.mp3 -acodec pcm_s16le -ac 1 -ar 16000 -y /home/kuavo/catkin_dt/src/voice_pkg/temp_record/playnew1.wav
ffmpeg -i /home/kuavo/catkin_dt/src/voice_pkg/temp_record/playtest.mp3 -acodec pcm_s16le -ac 1 -ar 16000 -filter:a "volume=15dB" -y /home/kuavo/catkin_dt/src/voice_pkg/temp_record/playnew5.wav
ffmpeg -i /home/kuavo/catkin_dt/src/voice_pkg/temp_record/play.wav -acodec pcm_s16le -ac 1 -ar 16000 -filter:a "volume=15dB" -y /home/kuavo/catkin_dt/src/voice_pkg/temp_record/ru_za_san_fu_she__chuan_bo_he_yi_zhi_she_ji_fen_xi_deng__pcm.wav
aplay -D plughw:0,0 -f S16_LE -r 16000 -c 1 /home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/iamherelouder.wav
    '''
    play_audio(savepath)
    # sd_play()
    # play_audio()
