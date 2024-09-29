使用命令行设置默认音频设备：[ref](https://www.baeldung.com/linux/change-default-audio-device-command-line)

## 调整输入，麦克风
首先使用 `pactl list short sources` 获取可用的麦克风列表
得到类似的输出
```
kuavo@kuavo-NUC12WSKi7:~$ pactl list short sources
0       alsa_input.usb-Bothlent_Bothlent_UAC_Dongle_88156088-00.multichannel-input      module-alsa-card.c      s16le 8ch 16000Hz       RUNNING
1       alsa_output.pci-0000_00_1f.3.analog-stereo.monitor      module-alsa-card.c      s16le 2ch 48000Hz       SUSPENDED
2       alsa_output.usb-DJI_Technology_Co.__Ltd._Wireless_Microphone_RX-00.analog-stereo.monitor        module-alsa-card.c      s16le 2ch 48000Hz       SUSPENDED
3       alsa_input.usb-DJI_Technology_Co.__Ltd._Wireless_Microphone_RX-00.analog-stereo module-alsa-card.c      s16le 2ch 48000Hz       SUSPENDED
```
找到DJI大疆的id，即上述输出中的alsa_input.usb-DJI_Technology_Co.__Ltd._Wireless_Microphone_RX-00
如上述输出所示，这个DJI大疆设备的id是3
然后使用命令将默认的输入设置为这个id `pactl set-default-source 3`

如果要使用头顶的麦克风，那么使用 sounddevice 库 或 pyaudio 库 录音的时候，
在调用时，调为 device = 5 

## 调整输出，喇叭
使用命令 `pactl list short sinks` 得到如下输出
```
kuavo@kuavo-NUC12WSKi7:~$ pactl list short sinks
0       alsa_output.pci-0000_00_1f.3.analog-stereo      module-alsa-card.c      s16le 2ch 48000Hz       SUSPENDED
1       alsa_output.usb-DJI_Technology_Co.__Ltd._Wireless_Microphone_RX-00.analog-stereo        module-alsa-card.c      s16le 2ch 48000Hz       SUSPENDED
```
使用命令 `pactl set-default-sink 0` 设置喇叭
其中 `0` 为 alsa_output.pci-0000_00_1f.3.analog-stereo 喇叭的id


## 使用命令行调节麦克风的灵敏度：
给默认的扬声器加5%，`amixer set Master 5%+`

给默认的麦克风加5%，`amixer set Capture 5%+`

## 开启唤醒词节点
  - 一个终端开启roscore
  - 另一个终端运行
  ```
  sros1
  . catkin_dt/devel/setup.bash
  rosrun voice_pkg microphone
  ```

唤醒词话题: `ivw_chatter`


## 人脸识别功能
  - 一个终端开启roscore
  ```
  sros1
  roscore
  ```
  - 另一个终端运行

  ```
  cd ~/kuavo_ros_application
  . ./devel_isolated/setup.sh
  roslaunch kuavo_robot_ros sensor_robot_enable.launch
  ```
  - 第三个终端运行
  **记得先关掉192.168.3.21:5901 VNC上的viewer**
  ```
  exp1
  python3 /home/kuavo/catkin_dt/src/visual_pkg/ER/EmotionRecognition.py
  ```

  人脸话题：`face_chatter`
