from pydub.playback import play
from pydub import AudioSegment
# import sys

savepath = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/sound_localization/manvoice.wav'
def playsound_work():
    play(AudioSegment.from_mp3(savepath)+10)
    
if __name__ == '__main__':
    # playsound_work()
    import numpy as np
    q = list()
    for i in range(10):
      q.append(i)
      if len(q) > 3:
        q = q[1:]
      print(np.mean(q))
      