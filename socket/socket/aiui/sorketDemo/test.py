import socket
import json
import struct
import gzip

# === 配置参数 ===
ANDROID_IP = '192.168.21.166'  # ← 请替换为你的安卓设备 IP
PORT = 19199                 # 默认 AIUI socket 服务端口

# === 构造 AIUI 协议封包 ===
def build_packet(payload_bytes, msg_id=1, msg_type=0x04):
    sync_head = b'\xA5'
    user_id = b'\x01'
    msg_len = struct.pack('<H', len(payload_bytes))  # 小端
    msg_id_bytes = struct.pack('<H', msg_id)
    body = sync_head + user_id + bytes([msg_type]) + msg_len + msg_id_bytes + payload_bytes
    checksum = (~sum(body) + 1) & 0xFF
    return body + bytes([checksum])

# === 解析 AIUI 协议响应 ===
def parse_packet(data):
    if len(data) < 8 or data[0] != 0xA5:
        print("无效或过短的数据包")
        return None

    msg_type = data[2]
    msg_len = struct.unpack('<H', data[3:5])[0]
    msg_id = struct.unpack('<H', data[5:7])[0]
    payload = data[7:7+msg_len]
    checksum = data[7+msg_len]

    calc_checksum = (~sum(data[:7+msg_len]) + 1) & 0xFF
    if checksum != calc_checksum:
        print(f"校验失败！期望: 0x{checksum:02X}, 实际: 0x{calc_checksum:02X}")
        return None

    print(f"[接收] 类型: 0x{msg_type:02X}, 长度: {msg_len}, ID: {msg_id}, 校验码: 0x{checksum:02X}")
    print("原始数据（十六进制）:", data.hex())

    if msg_type == 0xFF:
        print("收到确认消息（不包含业务内容）")
        return None
    elif msg_type == 0x04:
        try:
            decompressed = gzip.decompress(payload)
            json_str = decompressed.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            print("GZIP 解压或 JSON 解析失败：", e)
            print("Payload内容:", payload.hex())
            return None
    else:
        print(f"收到未处理的消息类型: 0x{msg_type:02X}")
        return None

# === 主函数 ===
def main():
    query_data = {
        "type": "status",
        "content": {
            "query": "voice"
        }
    }
    payload_bytes = json.dumps(query_data).encode('utf-8')
    packet = build_packet(payload_bytes)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ANDROID_IP, PORT))
        print(f"已连接到 Android AIUI 模块：{ANDROID_IP}:{PORT}")
        sock.sendall(packet)
        print("已发送“声音开关状态”查询请求...")

        sock.settimeout(3)
        received = False
        while not received:
            try:
                recv_data = sock.recv(2048)
                if not recv_data:
                    print("连接关闭或无数据")
                    break
                result = parse_packet(recv_data)
                if result:
                    voice_enabled = result.get("content", {}).get("enable_voice", None)
                    print("\n🔊 AIUI 声音播报开关状态：", "✅ 开启" if voice_enabled else "❌ 关闭")
                    received = True
                else:
                    print("继续等待业务响应...")
            except socket.timeout:
                print("等待超时，未收到业务响应。")
                break
    except Exception as e:
        print("通信异常：", e)
    finally:
        sock.close()
        print("连接已关闭。")

# === 程序入口 ===
if __name__ == "__main__":
    main()
