import socket
import json
import struct
import random

ANDROID_IP = '192.168.21.166'  # ← 修改为你的实际 IP 地址
PORT = 19199

def build_packet(payload_bytes, msg_id=6, msg_type=0x04):
    sync_head = b'\xA5'
    user_id = b'\x01'
    msg_len = struct.pack('<H', len(payload_bytes))
    msg_id_bytes = struct.pack('<H', msg_id)
    body = sync_head + user_id + bytes([msg_type]) + msg_len + msg_id_bytes + payload_bytes
    checksum = (~sum(body) + 1) & 0xFF
    return body + bytes([checksum])

def main():
    # 随机选择情感
    emot = random.choice(["neutral", "happy", "sorrow"])
    
    # 构造 TTS 请求
    tts_command = {
        "type": "tts",
        "content": {
            "action": "start",
            "text": "你好，欢迎使用AIUI语音播报系统！",  # 可以修改成你需要播报的内容
            "parameters": {
                "emot": emot,
                "speed": "50",  # 示例参数：语速，0~100，默认50
                "volume": "100"  # 音量（0~100）
            }
        }
    }

    payload_bytes = json.dumps(tts_command).encode('utf-8')
    packet = build_packet(payload_bytes)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ANDROID_IP, PORT))
        print(f"已连接至 AIUI 模块：{ANDROID_IP}:{PORT}")
        print(f"🗣️ 正在发送语音合成请求（情感: {emot}）...")
        sock.sendall(packet)
        print("✅ 合成播放命令已发送！请听设备是否开始播报。")
    except Exception as e:
        print("通信异常：", e)
    finally:
        sock.close()
        print("连接已关闭。")

if __name__ == "__main__":
    main()
