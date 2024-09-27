#!/bin/bash

# 进入catkin工作空间目录
cd ~/catkin_dt

# 加载环境设置
. devel/setup.bash

# 启动voice microphone，放在后台执行
rosrun voice_pkg microphone &
# 获取rosrun命令的进程ID
PID=$!

# 检查进程是否还在运行
if ps -p $PID > /dev/null; then
    echo "'voice microphone' is running."
    exit 0  # 正常退出，返回零状态
else
    echo "Failed to start 'voice microphone'. Command exited unexpectedly."
    exit 1  # 错误退出，返回非零状态
fi
