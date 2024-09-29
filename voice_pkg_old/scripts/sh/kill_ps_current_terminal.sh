#!/bin/bash

# 定义颜色
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取当前终端名称
current_tty=$(tty | awk -F/ '{print $NF}')

# 获取当前终端的所有进程
# processes=$(ps -t "$current_tty" -o pid,comm)

# 查找并杀死名为 python 的进程 (人脸检测)
pids=$(echo "$(ps -t "$current_tty" -o pid,comm)" | grep '[p]ython' | awk '{print $1}')
if [ -n "$pids" ]; then
    echo -e "${CYAN}Killing face detect process(es): $pids${NC}"
    kill -SIGKILL $pids
fi

# 查找名为 master_logged.py 的所有 Python 进程
PIDS=$(pgrep -f master_logged.py)

# 如果找到了相关进程，则使用 kill -9 强制结束这些进程
if [ ! -z "$PIDS" ]; then
    echo -e "${CYAN}Killing the following Python processes running master_logged.py:$PIDS${NC}"
    kill -9 $PIDS
else
    echo -e "${CYAN}No Python processes named master_logged.py found.${NC}"
fi

# 查找并杀死名为 microphone 的进程
pids=$(echo "$(ps -t "$current_tty" -o pid,comm)" | grep '[m]icrophone' | awk '{print $1}')
if [ -n "$pids" ]; then
    echo -e "${CYAN}Killing microphone process(es): $pids${NC}"
    kill $pids
fi

# 查找并杀死以 task3_ssh_port_ 开头的进程
pids=$(echo "$(ps -t "$current_tty" -o pid,comm)" | grep '[t]ask3_ssh_port_' | awk '{print $1}')
if [ -n "$pids" ]; then
    echo -e "${CYAN}Killing task3_ssh_port_ process(es): $pids${NC}"
    kill -SIGKILL $pids
fi

# 查找并杀死名为 ssh 的进程
pids=$(echo "$(ps -t "$current_tty" -o pid,comm)" | grep '[s]sh' | awk '{print $1}')
if [ -n "$pids" ]; then
    echo -e "${CYAN}Killing ssh process(es): $pids${NC}"
    kill $pids
fi

# 查找并杀死名为 clash 的进程
pids=$(echo "$(ps -t "$current_tty" -o pid,comm)" | grep '[c]lash' | awk '{print $1}')
if [ -n "$pids" ]; then
    echo -e "${CYAN}Killing clash process(es): $pids${NC}"
    kill $pids
fi

cd /home/kuavo/catkin_dt/src/voice_pkg/scripts/sh
./kill_port_forwarding.sh