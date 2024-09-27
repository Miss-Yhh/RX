
def text2speech(text='', index=0):
    # 如果喇叭不存在就直接跳过
    if not STATUS.SOUND_OUTPUT_EXIST:
        print(f"喇叭不存在: {text}")
        sleep(1)
        return

    savepath = os.path.join('/home/kuavo/catkin_dt/src/voice_pkg/temp_record/text2speech', str(time.time())+'.wav')

    ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/test_host_3090_tts.py", text, savepath])
    while ttsproc.poll() is None:
        # print('tts process is working, interrupted:', STATUS.is_Interrupted)
        if STATUS.is_Interrupted:
            print("kill tss")
            ttsproc.kill()
            return
        # time.sleep(0.1)

    while STATUS.Last_Play_Processor and STATUS.Last_Play_Processor.poll() is None:
        # print('last process is working, waiting')
        if STATUS.is_Interrupted:
            print("kill last play")
            STATUS.Last_Play_Processor.kill()
            return
        # time.sleep(0.1)
    playproc = subprocess.Popen(["aplay", "-D", f"plughw:{STATUS.card_id},0", '-f', 'S16_LE', '-r', '16000', '-c', '1', f'{savepath_pcm}'])

    # exit_status = os.system(cmd)
    if index == 1000: 
        # 同步播放
        while playproc.poll() is None:
            # print('play process is working')
            if STATUS.is_Interrupted:
                print('kill play process')
                playproc.kill()
                return
            # time.sleep(0.1)
        STATUS.set_Last_Play_Processor(None)
    else:
        # 异步播放:
        STATUS.set_Last_Play_Processor(playproc)
        # 等待的时间必不可少，因为会有playsound和tts的读写同一个文件的冲突，因此先playsound再让tts访问 play.wav
        time.sleep(0.15)
    return 'tts is over'
