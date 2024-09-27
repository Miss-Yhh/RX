#!/bin/bash

# 定义clash命令
clash_cmd="nohup ~/clash/clash -d ~/clash >~/clash/nohup.out 2>&1 &"

# 定义proxy命令
proxy_cmd="export http_proxy=http://127.0.0.1:7890; export https_proxy=http://127.0.0.1:7890; export all_proxy=socks5://127.0.0.1:7891"

# 运行clash命令
if ! eval $clash_cmd; then
    echo "Error: clash command failed."
    exit 1
fi

# 设置代理
if ! eval $proxy_cmd; then
    echo "Error: proxy command failed."
    exit 1
fi

echo "Clash and proxy commands completed successfully."
exit 0
