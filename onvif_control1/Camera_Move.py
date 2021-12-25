import time
from onvif import ONVIFCamera
import zeep
import requests
from requests.auth import HTTPDigestAuth
import logging
from sensecam_control import onvif_control
import numpy as np
import serial
import logging
import cv2


def zeep_pythonvalue(self, xmlvalue):
    return xmlvalue

def snap():
    '''
    使用python-onvif-zeep包抓图
    '''   
    zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue
    mycam = ONVIFCamera("192.168.0.69", 80, "admin", "mskj0417")  
    media = mycam.create_media_service()
    media_profile = media.GetProfiles()[0]
    res = media.GetSnapshotUri({'ProfileToken': media_profile.token})
    response = requests.get(res.Uri, auth=HTTPDigestAuth("admin", "mskj0417"))
    res = "{_time}.jpg".format(_time=time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time())))
    # with open(res, 'wb') as f:
        # f.write(response.content)
    im = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
    return im   # cv图片

def Sensecam():
    '''
    使用sensecam包对云台进行PTZ控制  https://github.com/smartsenselab/sensecam-control
    需git clone并install    
    '''
    ip = '192.168.0.69'
    login = 'admin'
    password = 'mskj0417'
    exit_program = 0
    camera_move = onvif_control.CameraControl(ip, login, password)
    camera_move.camera_start()
    return camera_move

def range_negatives(start1, end1, step1):
    for i in np.linspace(start1, end1, step1, dtype='float16'):
        yield i

def Move_camera(x, y, p):
    '''
    Move_camera((x1,y1), (x2,y2), (p1,p2))
    参数说明：
    x1：float
       x轴水平方向开始位置
    y1：float
       y轴竖直方向开始位置
    x2：float
       x轴水平方向结束位置
    y2：float
       y轴竖直方向结束位置
    p1、p2：int
       水平、竖直方向的移动次数，值越大，移动越精确。一般不建议p1>100，p2>20
        数值过大，会导致相机移动次数过多，耗费时间。
    
    例子：
    move_pan(-0.25, 0.90, 0.25 -0.90, 50, 8)---相机前向90°范围内扫描，水平方向每次旋转角度为1.8°

    返回值：
    return(Alarm_images, str_alarm)
    每次移动打印甲烷浓度值“The concentration of ch4 is X”

    若甲烷浓度值超标,则对疑似泄露位置拍照返图Alarm_images,并返回甲烷浓度值str_alarm
    若甲烷浓度值未超标,则返回None及当前最大甲烷浓度值.
    '''
    start_tilt = x[1]
    end_tilt = y[1]
    step_tilt = p[1]
    start_pan = x[0]
    end_pan = y[0]
    step_pan = p[0]
    str0 = []
    Alarm_images = None

    X = Sensecam()
    X.absolute_move(0, 1, 0)
    time.sleep(5)
    print('Mrobot_camera start moveing!')

    if start_tilt > 0 and end_tilt < 0:
        tilt1 = list(range_negatives(start_tilt, 1, step_tilt))
        count1 = step_tilt
        while count1 > 0:
            '''tilt'''
            for i in range(len(tilt1)):
                tilt_y1 = tilt1[i]
                X.absolute_move(start_pan, tilt_y1, 0)
                time.sleep(1)
                str_ch4 = read_ch4()
                print('The concentration of ch4 is %s \n' %str_ch4)
                str0.append(str_ch4)
                '''pan'''
                pan1 = list(range_negatives(start_pan, end_pan, step_pan))
                time.sleep(0.5)
                for i in range(len(pan1)):
                    pan_x = pan1[i]
                    X.absolute_move(pan_x, tilt_y1, 0)
                    time.sleep(0.5)
                    str_ch4 = read_ch4()
                    print('The concentration of ch4 is %s \n' %str_ch4)
                    str0.append(str_ch4)
                    count1 -= 1

        tilt2 = list(range_negatives(-1, end_tilt, step_tilt))
        count2 = step_tilt
        while count2 > 0:
            '''tilt'''
            for i in range(len(tilt2)):
                tilt_y2 = tilt2[i]
                X.absolute_move(start_pan, tilt_y2, 0)
                time.sleep(1)
                str_ch4 = read_ch4()
                print('The concentration of ch4 is %s \n' %str_ch4)
                str0.append(str_ch4)
                '''pan'''
                pan1 = list(range_negatives(start_pan, end_pan, step_pan))
                time.sleep(0.5)
                for i in range(len(pan1)):
                    pan_x = pan1[i]
                    X.absolute_move(pan_x, tilt_y2, 0)
                    time.sleep(0.5)
                    str_ch4 = read_ch4()
                    print('The concentration of ch4 is %s \n' %str_ch4)
                    str0.append(str_ch4)
                    count2 -= 1
    else:
        tilt = list(range_negatives(start_tilt, end_tilt, step_tilt))
        count = step_tilt
        while count > 0:
            '''tilt'''
            for i in range(len(tilt)):
                tilt_y = tilt[i]
                X.absolute_move(start_pan, tilt_y, 0)
                time.sleep(1)
                str_ch4 = read_ch4()
                print('The concentration of ch4 is %s \n' %str_ch4)
                str0.append(str_ch4)
                '''pan'''
                pan1 = list(range_negatives(start_pan, end_pan, step_pan))
                time.sleep(0.5)
                for i in range(len(pan1)):
                    pan_x = pan1[i]
                    X.absolute_move(pan_x, tilt_y, 0)
                    time.sleep(0.5)
                    str_ch4 = read_ch4()
                    print('The concentration of ch4 is %s \n' %str_ch4)
                    str0.append(str_ch4)
                    count -= 1
    
    time.sleep(2)
    X.absolute_move(0, 1, 0)    # 回归原点
    time.sleep(5)
    str_alarm = max(str0)
    if str_alarm >= 499:
        Alarm_images = snap()
    else:
        Alarm_images = None
    print('Mrobot_camera stop moveing!') 

    return(Alarm_images, str_alarm)

def move_to_point(point):
    x = point[0]
    y = point[1]
    X = Sensecam()
    X.absolute_move(x, y, 0)
    print('Please waiting!')
    time.sleep(3)
    img = snap()
    print('Complete! Stop moving!')
    return img

def Find_Points(x, y):
    '''
    输入点坐标（x，y），寻找位置点并返图。大范围移动需要等待云台转动，故设置5s等待返图的时间。
    '''
    X = Sensecam()
    X.absolute_move(x, y, 0)
    str = read_ch4()
    print('- - - - - - - - - - - -')
    print('The concentration of ch4 is %s \n' %str)
    print('Please waiting! The Camera is moving ~')
    time.sleep(3)
    snap()
    print(X.get_ptz())
    print('Complete! Stop moving!')


# read_cmd =  '01 04 00 04 00 02 30 0A'    # 查询读数寄存器指令,正常读取
# # read_cmd =  '01 04 00 07 00 01 80 0B'    # 查询读数寄存器指令,自校验读取
# class LaserDetector:
#     def __init__(self, Port='/dev/ttyUSB3'):    # 此处端口需根据所使用硬件修改
#                                                 # 串口号读取指令：ls -l /dev/ttyUSB*
#         self.serial = serial.Serial()
#         self.serial.port = Port
#         self.serial.baudrate = 9600
#         self.serial.timeout  = 2
#     def start(self):
#         if self.serial.isOpen():
#             serial.close()
#         self.serial.open()
#         logging.info('Serial Port is Opened')
#     def read(self):
#         cmd_send = bytes.fromhex(read_cmd)
#         self.serial.write(cmd_send)
#         dat = self.serial.read(9)
#         # print(dat)
#         return(dat)
#     def close(self):
#         self.serial.close()
# detector = LaserDetector('/dev/ttyUSB3')
# detector.start()

def read_ch4():
    '''
    使用串口命令读取检测仪寄存器内数据，返回甲烷浓度，直接调用“ read_ch4() ”方法即可。
    '''
    # conc_raw = detector.read()
    # conc = conc_raw[3]*256 + conc_raw[4]
    # print(conc)
    return(0)

'''END'''







