import time
import subprocess
import re
def set_master_index_by_keyword(keyword='pci-0000_00_1f'):
    # 运行 pactl list short sinks 命令
    result = subprocess.run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error executing arecord -l")
        return None

    # 打印输出结果，方便调试
    # print(result.stdout)

    # 使用正则表达式来查找含有关键字的行，并提取卡片的索引号
    match = re.search(r'(\d+).*' + re.escape(keyword), result.stdout)
    if match:
        masterid = int(match.group(1))
    else:
        return False
    # 同步执行的 run
    result = subprocess.run(['pactl', 'set-default-sink', str(masterid)], capture_output=True, text=True)
    return True
res = set_master_index_by_keyword()
if not res:
  print('hihi')
savepath = '/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/好的louder.wav'
ttsproc = subprocess.Popen(["python3", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_tts/play_sound.py", savepath])
# time.sleep(0.2)
# ttsproc.kill()