#!/bin/bash

# 进入目录
cd ~/catkin_dt/src

# 运行设置麦克风的脚本并捕获输出
output=$(./setmic.sh)

# 检查输出是否符合预期的成功消息
if [[ $output =~ "Source number found:" && $output =~ "Successfully set default source to" ]]; then
    echo "Microphone set successfully."
    echo "$output"
    exit 0
elif [[ $output == *"Error: 'input DJI' not found or the source number is empty."* ]]; then
    echo "Error: Microphone setting failed."
    echo "$output"
    exit 1
else
    echo "Unexpected output:"
    echo "$output"
    exit 2
fi
