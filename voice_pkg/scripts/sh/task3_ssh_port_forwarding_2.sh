#!/bin/bash

# 定义重启函数
restart_ssh_tunnel() {
    # 启动SSH端口转发，并同时将输出打印到终端和捕获到变量
    ssh_output=$(ssh -N -L 9833:gpu$1:9832 hpc 2>&1 | tee /dev/tty)
    SSH_PID=$!
    echo "SSH tunnel started with PID $SSH_PID"
    # 检查输出中是否包含端口占用错误
    if echo "$ssh_output" | grep -q "Address already in use"; then
        echo "Error: Address already in use. Could not request local forwarding."
        kill $SSH_PID
        exit 1
    fi
}

# 首次启动SSH端口转发
restart_ssh_tunnel $1 # 确保传递参数

# 循环监控SSH进程
while true; do
    # 检查进程是否还在运行
    if ! ps -p $SSH_PID > /dev/null; then
        echo "SSH tunnel exited unexpectedly. Restarting..."
        restart_ssh_tunnel $1  # 确保传递参数
    fi
    # 每隔一段时间检查一次，这里设置为10秒
    sleep 10
done
