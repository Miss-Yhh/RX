#!/bin/bash

# 指定 Conda 的初始化脚本，通常这一步是必需的，以确保 conda 命令能够在脚本中使用
# 你可能需要根据你的安装位置调整这个路径
source /home/robot/anaconda3/etc/profile.d/conda.sh

# 激活 Conda 环境
# 替换 YOUR_ENV_NAME 为你的 Conda 环境名称
conda activate zt38

# 执行 Python 脚本
# 替换 /path/to/your/script.py 为你的 Python 脚本路径
python /home/kuavo/catkin_dt/src/voice_pkg/scripts/funasr_asr/tts_sambert.py "$@"

# 可选：如果需要在脚本执行后停用环境，可以取消注释以下行
conda deactivate
