# --chunk_interval, "10": 600/10=60ms, "5"=600/5=120ms, "20": 600/12=30ms
python /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/test_host_3090_file.py --host "192.168.31.90" --port 10095 --mode offline --audio_in /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo.wav --output_dir /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/results
python /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/test_host_3090_file_online.py --host "192.168.31.90" --port 10095 --mode online --audio_in /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo.wav --output_dir /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/results
python funasr_wss_client.py --host "192.168.31.90" --port 10095 --mode offline --audio_in /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo.wav --output_dir /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/results
# --chunk_size, "5,10,5"=600ms, "8,8,4"=480ms
python funasr_wss_client.py --host "192.168.31.90" --port 10095 --mode 2pass --chunk_size "8,8,4" --audio_in /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/output_zhiyan_emo.wav

# --chunk_interval, "10": 600/10=60ms, "5"=600/5=120ms, "20": 600/12=30ms
python funasr_wss_client.py --host "192.168.31.90" --port 10095 --mode offline --output_dir /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/results

# --chunk_size, "5,10,5"=600ms, "8,8,4"=480ms
python funasr_wss_client.py --host "192.168.31.90" --port 10095 --mode 2pass --chunk_size "8,8,4"