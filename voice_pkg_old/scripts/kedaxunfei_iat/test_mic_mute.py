import subprocess


def run_process_and_filter_output(command):
    # 创建子进程
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print('waiting')
    # 实时读取输出并过滤
    try:
        while True:
            output = process.stdout.readline()
            print('hihi')
            if not output and process.poll() is not None:
                break
            if output and 'ALSA' not in output:
                print(output.strip())  # 打印非ALSA相关的输出
    except KeyboardInterrupt:
        process.kill()
        process.wait()

    # 处理任何剩余的输出
    _, stderr = process.communicate()
    if stderr:
        print("Error:", stderr.strip())

# 使用示例
cmd = ["python", "/home/kuavo/catkin_dt/src/voice_pkg/scripts/kedaxunfei_iat/get_mic_from_audio.py"]

run_process_and_filter_output(cmd)

