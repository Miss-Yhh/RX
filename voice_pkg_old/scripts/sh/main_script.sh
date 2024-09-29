#!/bin/bash

# 定义颜色
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查是否提供了第一个参数
if [ -z "$1" ]; then
    echo -e "${MAGENTA}Error: No port forwarding target specified.${NC}"
    exit 1
fi

# 检查是否提供了第二个参数
if [ -z "$2" ]; then
    echo -e "${MAGENTA}Error: No port forwarding target specified.${NC}"
    exit 1
fi

# 获取当前时间并设置日志文件路径
timestamp=$(date +"%Y%m%d_%H%M%S")
log_file="/home/kuavo/catkin_dt/src/voice_pkg/scripts/log/sh_log/main_script_$timestamp.log"

# 运行主脚本并将输出保存到日志文件
{
    amixer set Master 100% >> "$log_file" 2>&1

    echo -e "${CYAN}Kill all port forwarding.${NC}"
    ./kill_port_forwarding.sh >> "$log_file" 2>&1
    ./kill_port_forwarding.sh >> "$log_file" 2>&1

    echo -e "${CYAN}Starting Roscore...${NC}"
    ./task1_roscore.sh >> "$log_file" 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${MAGENTA}Error: Roscore initialization failed.${NC}"
        exit 1
    fi
    sleep 0.1

    echo -e "${CYAN}Starting Voice Microphone...${NC}"
    ./task2_voice_microphone.sh >> "$log_file" 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${MAGENTA}Error: Voice microphone initialization failed.${NC}"
        exit 1
    fi
    sleep 0.1

    ./task3_ssh_port_forwarding.sh $1 >> "$log_file" 2>&1 &
    echo -e "${CYAN}SSH port forwarding started in background.${NC}"
    sleep 0.1

    ./task3_ssh_port_forwarding_2.sh $2 >> "$log_file" 2>&1 &
    echo -e "${CYAN}SSH port forwarding started in background.${NC}"
    sleep 0.1

    echo -e "${CYAN}Starting Clash and Proxy...${NC}"
    ./task4_clash_proxy.sh >> "$log_file" 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${MAGENTA}Error: Clash proxy commands failed.${NC}"
        exit 1
    fi
    sleep 0.1

    echo -e "${CYAN}Setting Microphone Configuration...${NC}"
    ./task5_set_microphone.sh >> "$log_file" 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${MAGENTA}Error: Microphone setting failed.${NC}"
        exit 1
    fi

    # echo -e "${CYAN}Starting Face Client...${NC}"
    # ./task7_face_detect.sh >> "$log_file" 2>&1
    # if [ $? -ne 0 ]; then
    #     echo -e "${MAGENTA}Error: Face client commands failed.${NC}"
    #     exit 1
    # fi
    # sleep 0.2

    echo -e "${CYAN}Starting Touchpad Navi...${NC}"
    ./task8_touchpad_navi.sh >> "$log_file" 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${MAGENTA}Error: Touchpad Navi commands failed.${NC}"
        exit 1
    fi
    sleep 0.1

    # echo -e "${CYAN}Starting Mic Detect Pose...${NC}"
    # ./task9_mic_detect_pose.sh >> "$log_file" 2>&1
    # if [ $? -ne 0 ]; then
    #     echo -e "${MAGENTA}Error: Mic Detect Pose commands failed.${NC}"
    #     exit 1
    # fi
    # sleep 0.1

    # echo -e "${CYAN}Starting Mic Detect Hand...${NC}"
    # ./task10_mic_detect_hand.sh >> "$log_file" 2>&1
    # if [ $? -ne 0 ]; then
    #     echo -e "${MAGENTA}Error: Mic Detect Hand commands failed.${NC}"
    #     exit 1
    # fi
    # sleep 0.1

    echo -e "${CYAN}All scripts executed successfully.${NC}"

    # echo -e "${CYAN}Run master.${NC}"
    # /bin/python /home/kuavo/catkin_dt/src/voice_pkg/scripts/master_logged.py
} 2>&1 | tee -a "$log_file"

# cdsh
# ./main_script.sh