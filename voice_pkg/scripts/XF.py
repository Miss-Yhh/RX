import serial
import json

class XFSerialProtocol:
    def __init__(self,port='/dev/ttyACM0',baudrate=115200) -> None:
        self.serial = serial.Serial(port,baudrate)
        self.id = 0

    def check_sum(self,receive_data):
        check_sum = 0
        for i in range(len(receive_data)):
            check_sum += receive_data[i]
        return (~check_sum + 1) & 0xFF

    def send(self,data):
        if(self.serial.is_open == False):
            raise Exception("Serial port is not open")
        tosend = data + [self.check_sum(data)]
        self.serial.write(tosend)
        self.serial.flush()
        print("Sent: ",tosend)

    def send_ack(self):
        msg = [0xA5,0x01,0xff,0x00,0x00,0x00,0x00,0xa5,0x00,0x00,0x00]
        self.send(msg)

    def form_message(self,msg,msgid):
        msg = []
        msg.append(msgid & 0xff)
        msg.append((msgid >> 8) & 0xff)
        return msg

    def send_msg(self,msg):
        msg = [0xa5,0x01,0x05]
        msg.extend(self.form_message(msg,self.id))
        self.id += 1
        self.send(msg)

    def process(self):
        MAGIC = 0 # wait for magic
        HEADER = 1 # wait for msg type
        MESSAGE = 2 # wait for message
        status = MAGIC
        REQ = 0x01
        MSG = 0x04
        msg_type = None
        while True:
            if(status == MAGIC):
                b = self.serial.read(1)[0]
                if b == 0xA5:
                    b = self.serial.read(1)[0]
                    if b == 0x01:
                        status = HEADER
                        continue
                Warning("Invalid magic number, skipped")

            elif(status == HEADER):
                msg_type = self.serial.read(1)[0]
                if(msg_type == REQ):
                    self.send_ack()
                    continue
                elif(msg_type == MSG):
                    status = MESSAGE
                    continue
                else:
                    Warning("Invalid message type, skipped")
                    status = MAGIC

            elif(status == MESSAGE):
                bsize = self.serial.read(2)
                size = int.from_bytes(bsize,byteorder='little')
                bmsg_id = self.serial.read(2)
                msg_id = int.from_bytes(bmsg_id,byteorder='little')
                msg = self.serial.read(size)
                data_to_checksum = [0xa5,0x01,msg_type,*bsize,*bmsg_id,*msg]
                checksum = self.serial.read(1)[0]
                calculated_checksum = self.check_sum(data_to_checksum)
                if(checksum == calculated_checksum):
                    return msg_id,msg
                else:
                    Warning("Invalid checksum, skipped")
                status = MAGIC
                    

class XFJsonProtocol:
    def __init__(self) -> None:
        pass

    def processJson(self,json_data):
        data = json.loads(json_data)
        return data

    def changWakeupKeywords(self,keywords="ni3 hao3 ling2 bo2",threshold="900"):
        ''''''
        data = {
            "type": "wakeup_keywords",
            "content": {
            "keyword": "xiao3 fei1 xiao3 fei1",
            "threshold": "900"
            }
        }
        return json.dumps(data)
    



# class ThreadWakeCheck(threading.Thread):
#     def __init__(self,xf) -> None:
#         super().__init__()
#         self.xf = xf
#         self.xfj = XFJsonProtocol()
#         self.wake = False

#     def run(self):
#         while True:
            

if __name__ == "__main__":
    xf = XFSerialProtocol()
    xfj = XFJsonProtocol()
    while True:
        msg_id,msg = xf.process()
        msg_json = xfj.processJson(msg)
        print("hello")

    # test_th = ThreadWakeCheck(xf)
    # test_th.start()