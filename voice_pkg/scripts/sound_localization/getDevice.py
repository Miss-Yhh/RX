import numbers
import pyaudio
#//cat /proc/asound/devices 
p=pyaudio.PyAudio()

def listdevice(index):
    print(p.get_host_api_count())
    info = p.get_host_api_info_by_index(index)
    numberdevices = info.get('deviceCount')
    print('Number of devices:',numberdevices)
    for i in range(0,numberdevices):
        if(p.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels'))>0:
            print('INPUT DVEICES ID:',i,"-",p.get_device_info_by_host_api_device_index(0,i).get('name'))
            get_device_info_by_index(i)
def listdevice2():
    import pyaudio
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"Index: {i}, Name: {info['name']}")
# 获取设备信息
def get_device_info_by_index(index):
    device_info = p.get_device_info_by_index(index)
    print("设备名称:", device_info.get('name'))
    print("设备采样率:", device_info.get('defaultSampleRate'))
    print("设备最大输入通道:", device_info.get('maxInputChannels'))
    print("设备最大输出通道:", device_info.get('maxOutputChannels'))

def checkh5py():
    import h5py
    import numpy as np
    filename = '/home/robot/soundposition/recordV1.h5'
    with h5py.File(filename, 'r') as hf:
        hf.visit(print)  
        audio_data = hf['time_data'][:]
        print(audio_data.shape)
        print(audio_data.mean())
        print(hf.values)
# 获取第二个设备的信息（索引为1）
# get_device_info_by_index(0)
# get_device_info_by_index(5)
# get_device_info_by_index(6)
# get_device_info_by_index(10)
# get_device_info_by_index(11)
# get_device_info_by_index(12)
# get_device_info_by_index(13)
# checkh5py()
listdevice(0)