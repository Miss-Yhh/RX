import os
from pydub import AudioSegment
from pydub.playback import play
import subprocess
from multiprocessing import Process

def get_audio_length(file_path:str):
    audio = AudioSegment.from_file(file_path)
    length_ms = len(audio)
    return length_ms / 1000.0 

def play_sound(mp3_path:str):
    # play(AudioSegment.from_mp3(mp3_path))   
    #os.system(f"ffplay -nodisp -autoexit {mp3_path}")
    #subprocess.run(["ffplay", "-nodisp", "-autoexit", mp3_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", mp3_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=10 ) # 设置超时为 10 秒

def mp3_to_wav(mp3_path, wav_path):
    os.system(f"ffmpeg -i {mp3_path} -acodec pcm_s16le -ar 16000 -ac 1 -y {wav_path}")

def wav_to_mp3(wav_path, mp3_path):
    os.system(f"ffmpeg -i {wav_path} -acodec libmp3lame -ab 128k -y {mp3_path}")

if __name__ == "__main__":
    # wav_to_mp3("please_say.wav", "please_say.mp3")
    # wav_to_mp3("finish_instruction.wav", "finish_instruction.mp3")
    play_sound("/home/hit/RX/save_waves/finish_instruction.mp3")