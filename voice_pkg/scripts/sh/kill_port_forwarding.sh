#!/bin/bash

# 定义一个函数来杀死匹配到的进程
kill_matched_processes() {
    local pattern=$1
    local pids=$(pgrep -f "$pattern")

    # 检查是否找到了进程
    if [ -z "$pids" ]; then
        echo "没有找到任何以 '$pattern' 开头的进程。"
    else
        # 显示将要杀死的进程ID
        echo "找到以下进程，将会被杀死:"
        echo "$pids"
        
        # 循环遍历每个进程ID，并杀死它
        for pid in $pids; do
            kill -SIGKILL $pid
            echo "已杀死进程 $pid"
        done
    fi
}

# 杀死所有以 "ssh -N -L 8000" 开头的进程
echo "检查以 'ssh -N -L 8000' 开头的 SSH 进程..."
kill_matched_processes "ssh -N -L 8000"

# 杀死所有以 "ssh -N -L 9111" 开头的进程
echo "检查以 'ssh -N -L 9111' 开头的 SSH 进程..."
kill_matched_processes "ssh -N -L 9111"

# 杀死所有以 "ssh -N -L 9833" 开头的进程
echo "检查以 'ssh -N -L 9833' 开头的 SSH 进程..."
kill_matched_processes "ssh -N -L 9833"

# 杀死所有名为 "task3_ssh_port_forwarding.sh" 的进程
echo "检查运行脚本 'task3_ssh_port_forwarding.sh' 的进程..."
kill_matched_processes "/bin/bash ./task3_ssh_port_forwarding.sh"

# 杀死所有名为 "visual_pkg/scripts/test_websocket.py" 的进程
echo "检查运行程序 'visual_pkg/scripts/test_websocket.py' 的进程..."
kill_matched_processes "python.*visual_pkg/scripts/test_websocket.py"

# 杀死所有名为 "voice_pkg/scripts/chukongban/android_chatter.py" 的进程
echo "检查运行程序 'voice_pkg/scripts/chukongban/android_chatter.py' 的进程..."
kill_matched_processes "python.*voice_pkg/scripts/chukongban/android_chatter.py"