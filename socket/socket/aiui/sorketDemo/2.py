import socket
import json
import struct

ANDROID_IP = '192.168.21.166'  # 替换为你的 AIUI Android 设备 IP
PORT = 19199

# === 构造 AIUI 协议数据包 ===
def build_packet(payload_bytes, msg_id=10, msg_type=0x04):  # 类型固定为0x04
    sync_head = b'\xA5'
    user_id = b'\x01'
    msg_len = struct.pack('<H', len(payload_bytes))  # 小端模式
    msg_id_bytes = struct.pack('<H', msg_id)
    body = sync_head + user_id + bytes([msg_type]) + msg_len + msg_id_bytes + payload_bytes
    checksum = (~sum(body) + 1) & 0xFF
    return body + bytes([checksum])

# === 构造配置消息 ===
def get_aiui_config_packet():
    config_json = {
        "type": "aiui_cfg",
        "content": {
            "login": {
                "appid": "6e15868d",   # ← 请替换为你的真实 AppID
                "key": "3fd4b9d03d1da69f1fc444ebe374823a"        # ← 请替换为你的真实 Key
            },
            "launch_demo": False  # 是否启动默认播报 Demo
        }
    }
    payload_bytes = json.dumps(config_json).encode('utf-8')
    return build_packet(payload_bytes)

# === 主函数 ===
def main():
    packet = get_aiui_config_packet()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ANDROID_IP, PORT))
        print(f"已连接至 AIUI 模块：{ANDROID_IP}:{PORT}")
        sock.sendall(packet)
        print("✅ 已发送 AIUI 配置命令。")
        print("⚠️ 该配置需要重启 AIUI 服务后才能生效。")
    except Exception as e:
        print("通信异常：", e)
    finally:
        sock.close()
        print("连接已关闭。")

if __name__ == "__main__":
    main()
