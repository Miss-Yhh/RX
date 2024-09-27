#!/bin/bash

# 创建命名管道
PIPE=$(mktemp -u)
mkfifo $PIPE

# 尝试启动roscore并捕获输出和错误，放在后台执行
{ roscore > $PIPE 2>&1 & echo $! > pid_file; } &
PID=$(cat pid_file)

# 检查输出是否包含已运行的错误消息，并在超时后检查进程状态
if timeout 2 grep -q "roscore/master is already running" < $PIPE; then
    echo "Roscore is already running."
    kill $PID
    rm $PIPE
    rm pid_file
    exit 0  # 正常退出
elif ps -p $PID > /dev/null; then
    echo "Roscore started successfully and is running."
else
    echo "Failed to start Roscore."
    kill $PID
    rm $PIPE
    rm pid_file
    exit 1  # 错误退出，返回非零状态
fi

# 清理命名管道
rm $PIPE
rm pid_file

exit 0  # 正常退出
