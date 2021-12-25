import time
from datetime import timedelta
import logging
import zeep
import serial
import logging
import cv2
import numpy as np
import requests
from requests.auth import HTTPDigestAuth
from onvif import ONVIFCamera
from sensecam_control import onvif_control


class CameraPtz(object):
    '''
    用于云台控制，包含以下方法：
    snap() 抓图；
    scan() 云台区域内逐点扫描；
    move_to_point() 云台移动到指定点位
    
    参数：
    ip, username, password --云台ip、用户名、密码
    point1, point2, step_nums --云台扫描区域及扫描步长
    detect_point --云台移动点位
    '''
    def __init__(self, ip, username, password, point1, point2, step_nums, detect_point):
        self.ip = ip
        self.username = username
        self.password = password
        self.point1 = point1
        self.point2 = point2
        self.step_nums = step_nums
        self.detect_point = detect_point

    def zeep_pythonvalue(self, xmlvalue):
        return xmlvalue

    def range_negatives(start, end, step):
        for i in np.linspace(start, end, step, dtype='float16'):
            yield i

    def snap(self):
        '''抓图'''
        zeep.xsd.simple.AnySimpleType.pythonvalue = CameraPtz.zeep_pythonvalue
        mycam = ONVIFCamera(self.ip, 80, self.username, self.password)  
        media = mycam.create_media_service()
        media_profile = media.GetProfiles()[0]
        res = media.GetSnapshotUri({'ProfileToken': media_profile.token})
        response = requests.get(res.Uri, auth=HTTPDigestAuth(self.username, self.password))
        res = "{_time}.jpg".format(_time=time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time())))
        with open(res, 'wb') as f:
            f.write(response.content)
        im = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
        return im

    def sensecam(self):
        '''onvif协议包，用于云台ptz'''
        camera_move = onvif_control.CameraControl(self.ip, self.username, self.password)
        camera_move.camera_start()
        return camera_move  

    def scan(self):
        '''控制云台扫描撬装区，返回疑似泄露位置图像alarm_image、泄露值str_alarm'''
        start_tilt = self.point1[1]
        end_tilt = self.point2[1]
        step_tilt = self.step_nums[1]
        start_pan = self.point1[0]
        end_pan = self.point2[0]
        step_pan = self.step_nums[0]
        str0 = []
        str1 = []
        alarm_image = None

        X = CameraPtz.sensecam(self)
        X.absolute_move(-0.835, 0.16, 0) # 默认相机原点
        time.sleep(1)
        print('camera start moveing!')

        if start_tilt > 0 and end_tilt < 0:
            tilt1 = list(CameraPtz.range_negatives(start_tilt, 1, step_tilt))
            count1 = step_tilt
            while count1 > 0:
                for i in range(len(tilt1)):
                    tilt_y1 = tilt1[i]
                    '''ptz'''
                    pan1 = list(CameraPtz.range_negatives(start_pan, end_pan, step_pan))
                    for i in range(len(pan1)):
                        pan_x = pan1[i]
                        X.absolute_move(pan_x, tilt_y1, 0)
                        str_ch4 = LaserDetector.read_ch4()
                        print('The concentration of ch4 is %s \n' %str_ch4)
                        str0.append(str_ch4)
                        str1.append([pan_x, tilt_y1])
                        count1 -= 1
            tilt2 = list(CameraPtz.range_negatives(-1, end_tilt, step_tilt))
            count2 = step_tilt
            while count2 > 0:
                for i in range(len(tilt2)):
                    tilt_y2 = tilt2[i]
                    '''ptz'''
                    pan1 = list(CameraPtz.range_negatives(start_pan, end_pan, step_pan))
                    for i in range(len(pan1)):
                        pan_x = pan1[i]
                        X.absolute_move(pan_x, tilt_y2, 0)
                        str_ch4 = LaserDetector.read_ch4()
                        print('The concentration of ch4 is %s \n' %str_ch4)
                        str0.append(str_ch4)
                        str1.append([pan_x, tilt_y2])
                        count2 -= 1
        else:
            tilt = list(CameraPtz.range_negatives(start_tilt, end_tilt, step_tilt))
            count = step_tilt
            while count > 0:
                for i in range(len(tilt)):
                    tilt_y = tilt[i]
                    '''ptz'''
                    pan1 = list(CameraPtz.range_negatives(start_pan, end_pan, step_pan))
                    for i in range(len(pan1)):
                        pan_x = pan1[i]
                        X.absolute_move(pan_x, tilt_y, 0)
                        str_ch4 = LaserDetector.read_ch4()
                        print('The concentration of ch4 is %s \n' %str_ch4)
                        str0.append(str_ch4)
                        str1.append([pan_x, tilt_y])
                        count -= 1
        time.sleep(2)
        X.absolute_move(-0.84, 0.16, 0)
        str_ch4 = LaserDetector.read_ch4()
        str0.append(str_ch4)
        str1.append((-0.84, 0.16))
        time.sleep(1)
        str0_index = str0.index(max(str0))
        index_point = str1[str0_index]
        X.absolute_move(index_point[0], index_point[1], 0)
        time.sleep(2)
        str_alarm = max(str0)
        if str_alarm >= 499:
            alarm_image = CameraPtz.snap()
        else:
            alarm_image = None
        print('camera stop moveing!') 
        return(alarm_image, str_alarm)

    def move_to_point(self):
        '''控制云台移动到指定的detect_point'''
        pan = self.detect_point[0]
        tilt = self.detect_point[1]
        X = CameraPtz.sensecam()
        X.absolute_move(pan, tilt, 0)
        time.sleep(2)
        print('Complete! Camera aleady move_to_point!')


class LaserDetector(object):
    '''
    通过485串口读取激光检漏仪的寄存器，并返回燃气浓度值conc
    '''
    def __init__(self, Port='/dev/ttyUSB0'):    # 此处端口需根据所使用硬件修改；串口号读取指令：ls -l /dev/ttyUSB*
        self.serial = serial.Serial()
        self.serial.port = Port
        self.serial.baudrate = 9600
        self.serial.timeout  = 0.18
        self.read_cmd =  '01 04 00 04 00 02 30 0A'    # 查询读数寄存器指令,正常读取
        self.port = Port

    def start(self):
        if self.serial.isOpen():
            serial.close()
        try:
            self.serial.open()
            logging.info('Serial Port is Opened')
        except:
            logging.error('Serial Port is wrong，continue...')
            pass

    def read(self):
        cmd_send = bytes.fromhex(self.read_cmd)
        self.serial.write(cmd_send)
        dat = self.serial.read(9)
        return(dat)

    def close(self):
        self.serial.close()

    def read_ch4(self):
        detector = LaserDetector(self.port)
        detector.start()
        try:
            count = 3
            tmp = []
            for i in range(count):
                conc_raw = detector.read()
                conc = conc_raw[3]*256 + conc_raw[4]
                time.sleep(0.18)
                tmp.append(conc)
            conc = max(tmp)
        except Exception as e:
            logging.error(e)
            conc = -1
            return conc
        else:
            return conc    

'''END'''