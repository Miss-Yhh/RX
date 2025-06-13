import socket
import json
import struct

ANDROID_IP = '192.168.21.166'  # 你的 Android 上位机 IP
PORT = 19199

def build_packet(payload_bytes, msg_id=2, msg_type=0x04):
    sync_head = b'\xA5'
    user_id = b'\x01'
    msg_len = struct.pack('<H', len(payload_bytes))
    msg_id_bytes = struct.pack('<H', msg_id)
    body = sync_head + user_id + bytes([msg_type]) + msg_len + msg_id_bytes + payload_bytes
    checksum = (~sum(body) + 1) & 0xFF
    return body + bytes([checksum])

def main():
    # 要发送的开启声音的指令
    command = {
        "type": "command",
        "content": {
            "command": "set_voice",
            "enable_voice": True
        }
    }
    payload_bytes = json.dumps(command).encode('utf-8')
    packet = build_packet(payload_bytes)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ANDROID_IP, PORT))
        print(f"已连接到 AIUI 模块：{ANDROID_IP}:{PORT}")
        sock.sendall(packet)
        print("✅ 已发送开启声音播报的设置命令。")
    except Exception as e:
        print("通信异常：", e)
    finally:
        sock.close()
        print("连接已关闭。")

if __name__ == "__main__":
    main()
